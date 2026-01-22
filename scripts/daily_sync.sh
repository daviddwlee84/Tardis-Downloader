#!/bin/bash
# ============================================================================
# Daily Sync Script for Tardis Data Downloads
# ============================================================================
#
# Purpose: Incremental sync of crypto market data from Tardis.dev
#
# Usage:
#   ./scripts/daily_sync.sh                    # Run all profiles
#   ./scripts/daily_sync.sh btc_full           # Run specific profile
#   ./scripts/daily_sync.sh --dry-run          # Dry run mode
#
# Cron example (run daily at 2 AM):
#   0 2 * * * /home/taa/David/Tardis-Downloader/scripts/daily_sync.sh >> /var/log/tardis_sync.log 2>&1
#
# ============================================================================

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="${PROJECT_DIR}/configs/ml_quant_download.yaml"
LOG_DIR="${PROJECT_DIR}/logs"
ENV_FILE="${PROJECT_DIR}/.env"

# Profiles to sync (in order)
PROFILES=("btc_full" "eth_sol_full" "altcoins_main")

# Parse arguments
DRY_RUN=""
SPECIFIC_PROFILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        *)
            SPECIFIC_PROFILE="$1"
            shift
            ;;
    esac
done

# Create log directory
mkdir -p "$LOG_DIR"

# Timestamp for logging
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="${LOG_DIR}/sync_${TIMESTAMP}.log"

# Function to log messages
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

# Function to run incremental download for a profile
sync_profile() {
    local profile=$1
    log "Starting incremental sync for profile: $profile"

    if [[ -n "$DRY_RUN" ]]; then
        log "DRY RUN MODE - no actual downloads will occur"
    fi

    cd "$PROJECT_DIR"

    # Load environment variables
    if [[ -f "$ENV_FILE" ]]; then
        set -a
        source "$ENV_FILE"
        set +a
    fi

    # Run incremental download
    if td-fire incremental --config "$CONFIG_FILE" --profile "$profile" $DRY_RUN >> "$LOG_FILE" 2>&1; then
        log "Completed sync for profile: $profile"
        return 0
    else
        log "ERROR: Failed to sync profile: $profile"
        return 1
    fi
}

# Main execution
log "============================================"
log "Starting Tardis Daily Sync"
log "Config: $CONFIG_FILE"
log "============================================"

# Check if config exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    log "ERROR: Config file not found: $CONFIG_FILE"
    exit 1
fi

# Check if td-fire command exists
if ! command -v td-fire &> /dev/null; then
    log "ERROR: td-fire command not found. Make sure the package is installed."
    log "Try: cd $PROJECT_DIR && uv sync"
    exit 1
fi

# Track success/failure
FAILED_PROFILES=()
SUCCESS_COUNT=0

# Run sync for profiles
if [[ -n "$SPECIFIC_PROFILE" ]]; then
    # Single profile mode
    if sync_profile "$SPECIFIC_PROFILE"; then
        SUCCESS_COUNT=1
    else
        FAILED_PROFILES+=("$SPECIFIC_PROFILE")
    fi
else
    # All profiles mode
    for profile in "${PROFILES[@]}"; do
        if sync_profile "$profile"; then
            ((SUCCESS_COUNT++))
        else
            FAILED_PROFILES+=("$profile")
        fi

        # Small delay between profiles to avoid rate limiting
        sleep 5
    done
fi

# Update index after downloads (only if not dry run)
if [[ -z "$DRY_RUN" ]]; then
    log "Updating metadata index..."
    if td-fire index-build --config "$CONFIG_FILE" --update-only >> "$LOG_FILE" 2>&1; then
        log "Index updated successfully"
    else
        log "WARNING: Index update failed"
    fi
fi

# Summary
log "============================================"
log "Sync Complete"
log "Successful: $SUCCESS_COUNT"
log "Failed: ${#FAILED_PROFILES[@]}"

if [[ ${#FAILED_PROFILES[@]} -gt 0 ]]; then
    log "Failed profiles: ${FAILED_PROFILES[*]}"
    exit 1
fi

log "============================================"
exit 0
