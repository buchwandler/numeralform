"""Built-in locale renderers."""

from importlib import import_module

from .am import AmharicRenderer
from .ar import ArabicRenderer
from .az import AzerbaijaniRenderer
from .be import BelarusianRenderer
from .bg import BulgarianRenderer
from .bn import BengaliRenderer
from .ca import CatalanRenderer
from .ce import ChechenRenderer
from .cs import CzechRenderer
from .cy import WelshRenderer
from .da import DanishRenderer
from .de import GermanRenderer
from .el import GreekRenderer
from .en import EnglishRenderer
from .eo import EsperantoRenderer
from .es import SpanishRenderer
from .et import EstonianRenderer
from .eu import BasqueRenderer
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
from .ka import GeorgianRenderer
from .kk import KazakhRenderer
from .kn import KannadaRenderer
from .ko import KoreanRenderer
from .ku import KurdishRenderer
from .lb import LuxembourgishRenderer
from .lt import LithuanianRenderer
from .lv import LatvianRenderer
from .ml import MalayalamRenderer
from .mn import MongolianRenderer
from .mr import MarathiRenderer
from .ne import NepaliRenderer
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
from .sq import AlbanianRenderer
from .sr import SerbianRenderer
from .sv import SwedishRenderer
from .sw import SwahiliRenderer
from .te import TeluguRenderer
from .tet import TetumRenderer
from .tg import TajikRenderer
from .th import ThaiRenderer
from .tr import TurkishRenderer
from .uk import UkrainianRenderer
from .unsupported import UnsupportedLocaleRenderer
from .ur import UrduRenderer
from .vi import VietnameseRenderer
from .zh import ChineseRegionalRenderer, ChineseRenderer

__all__ = [
    "AlbanianRenderer",
    "AmharicRenderer",
    "ArabicRenderer",
    "ArmenianRenderer",
    "AzerbaijaniRenderer",
    "BasqueRenderer",
    "BelarusianRenderer",
    "BengaliRenderer",
    "BulgarianRenderer",
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
    "EstonianRenderer",
    "FinnishRenderer",
    "FrenchBelgiumRenderer",
    "FrenchRenderer",
    "FrenchSwissRenderer",
    "GeorgianRenderer",
    "GermanRenderer",
    "GreekRenderer",
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
    "KurdishRenderer",
    "LatvianRenderer",
    "LithuanianRenderer",
    "LuxembourgishRenderer",
    "MalayalamRenderer",
    "MarathiRenderer",
    "MongolianRenderer",
    "NepaliRenderer",
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
    "SwahiliRenderer",
    "SwedishRenderer",
    "TajikRenderer",
    "TeluguRenderer",
    "TetumRenderer",
    "ThaiRenderer",
    "TurkishRenderer",
    "UkrainianRenderer",
    "UnsupportedLocaleRenderer",
    "UrduRenderer",
    "VietnameseRenderer",
    "WelshRenderer",
]
