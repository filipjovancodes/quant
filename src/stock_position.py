from ib_insync import *

from src.asset_position import AssetPosition


class StockPosition(AssetPosition):
    def __init__(self, ib, position: Position) -> None:
        super().__init__(ib)
        self.position = position
        self.price = self.get_price()
    
    def __str__(self) -> str:
        str = "StockPosition:\n"
        str += f"Position: {self.position}\n"
        str += f"Price: {self.price}\n"
        return str