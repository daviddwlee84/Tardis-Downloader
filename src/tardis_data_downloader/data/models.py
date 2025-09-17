# TODO: Based on schema create Pydantic models

from enum import StrEnum
from pydantic import BaseModel


class SYMBOL_TYPE(StrEnum):
    SPOT = "spot"
    PERPETUAL = "perpetual"
    FUTURES = "futures"
    OPTION = "option"
    COMBO = "combo"


class SymbolInfo(BaseModel):
    id: str
    type: SYMBOL_TYPE
    availableSince: str
    availableTo: str

    # BUG:
    # pydantic_core._pydantic_core.ValidationError: 1 validation error for SymbolInfo
    # availableTo
    # Field required [type=missing, input_value={'id': 'BTC-PERPETUAL', '...19-03-30T00:00:00.000Z'}, input_type=dict]
    #     For further information visit https://errors.pydantic.dev/2.11/v/missing
