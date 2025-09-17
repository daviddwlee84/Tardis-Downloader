from tardis_dev import datasets
from dotenv import load_dotenv, find_dotenv
import fire

_ = load_dotenv(find_dotenv())

fire.Fire(datasets.download)
