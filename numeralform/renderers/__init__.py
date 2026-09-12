"""Built-in locale renderers."""

from importlib import import_module

from .am import AmharicRenderer
from .ar import ArabicRenderer
from .az import AzerbaijaniRenderer
from .be import BelarusianRenderer
from .bn import BengaliRenderer
from .ca import CatalanRenderer
from .ce import ChechenRenderer
from .cs import CzechRenderer
from .cy import WelshRenderer
from .da import DanishRenderer
from .de import GermanRenderer
from .en import EnglishRenderer
from .eo import EsperantoRenderer
from .es import SpanishRenderer
from .fa import PersianRenderer
from .fi import FinnishRenderer
from .fr import FrenchRenderer
from .he import HebrewRenderer
from .hi import HindiRenderer
from .hu import HungarianRenderer
from .hy import ArmenianRenderer
from .id import IndonesianRenderer

IcelandicRenderer = import_module(".is", __name__).IcelandicRenderer
from .it import ItalianRenderer
from .ja import JapaneseRenderer
from .kk import KazakhRenderer
from .kn import KannadaRenderer
from .ko import KoreanRenderer
from .lt import LithuanianRenderer
from .lv import LatvianRenderer
from .mn import MongolianRenderer
from .nl import DutchRenderer
from .no import NorwegianRenderer
from .ordinal import OrdinalNotationRenderer
from .pl import PolishRenderer
from .pt import PortugueseRenderer
from .regional import (
    EnglishGBRenderer,
    EnglishIndiaRenderer,
    EnglishNigeriaRenderer,
    EnglishUSRenderer,
    FrenchBelgiumRenderer,
    FrenchSwissRenderer,
)
from .ro import RomanianRenderer
from .ru import RussianRenderer
from .sk import SlovakRenderer
from .sl import SlovenianRenderer
from .sr import SerbianRenderer
from .sv import SwedishRenderer
from .te import TeluguRenderer
from .tet import TetumRenderer
from .tg import TajikRenderer
from .th import ThaiRenderer
from .tr import TurkishRenderer
from .uk import UkrainianRenderer
from .unsupported import UnsupportedLocaleRenderer
from .vi import VietnameseRenderer
from .zh import ChineseRegionalRenderer, ChineseRenderer

__all__ = [
    "AmharicRenderer",
    "ArabicRenderer",
    "ArmenianRenderer",
    "AzerbaijaniRenderer",
    "BelarusianRenderer",
    "BengaliRenderer",
    "CatalanRenderer",
    "ChechenRenderer",
    "ChineseRegionalRenderer",
    "ChineseRenderer",
    "CzechRenderer",
    "DanishRenderer",
    "DutchRenderer",
    "EnglishGBRenderer",
    "EnglishIndiaRenderer",
    "EnglishNigeriaRenderer",
    "EnglishRenderer",
    "EnglishUSRenderer",
    "EsperantoRenderer",
    "FinnishRenderer",
    "FrenchBelgiumRenderer",
    "FrenchRenderer",
    "FrenchSwissRenderer",
    "GermanRenderer",
    "HebrewRenderer",
    "HindiRenderer",
    "HungarianRenderer",
    "IcelandicRenderer",
    "IndonesianRenderer",
    "ItalianRenderer",
    "JapaneseRenderer",
    "KannadaRenderer",
    "KazakhRenderer",
    "KoreanRenderer",
    "LatvianRenderer",
    "LithuanianRenderer",
    "MongolianRenderer",
    "NorwegianRenderer",
    "OrdinalNotationRenderer",
    "PersianRenderer",
    "PolishRenderer",
    "PortugueseRenderer",
    "RomanianRenderer",
    "RussianRenderer",
    "SerbianRenderer",
    "SlovakRenderer",
    "SlovenianRenderer",
    "SpanishRenderer",
    "SwedishRenderer",
    "TajikRenderer",
    "TeluguRenderer",
    "TetumRenderer",
    "ThaiRenderer",
    "TurkishRenderer",
    "UkrainianRenderer",
    "UnsupportedLocaleRenderer",
    "VietnameseRenderer",
    "WelshRenderer",
]
