from iconservice import *

TAG = 'ICONBET'


# An interface of ICON Token Standard, IRC-2
class TokenStandard(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def symbol(self) -> str:
        pass

    @abstractmethod
    def decimals(self) -> int:
        pass

    @abstractmethod
    def totalSupply(self) -> int:
        pass

    @abstractmethod
    def balanceOf(self, _owner: Address) -> int:
        pass

    @abstractmethod
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


# An interface of tokenFallback.
# Receiving SCORE that has implemented this interface can handle
# the receiving or further routine.
class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass


class ICONBET(IconScoreBase, TokenStandard):
    _ICEAGE = 'iceage'
    _BALANCES = 'balances'
    _TOTAL_SUPPLY = 'total_supply'
    _DECIMALS = 'decimals'
    _FROZENERS = 'frozeners'
    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass
    
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._is_ice_age = VarDB(self._ICEAGE, db, value_type=bool)
        self._frozeners = DictDB(self._FROZENERS, db, value_type=bool)
        self._total_supply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._decimals = VarDB(self._DECIMALS, db, value_type=int)
        self._balances = DictDB(self._BALANCES, db, value_type=int)

    def on_install(self, _initialSupply: int, _decimals: int) -> None:
        super().on_install()
        if _initialSupply < 0:
            revert("Initial supply cannot be less than zero")
        if _decimals < 0:
            revert("Decimals cannot be less than zero")
        if _decimals > 21:
            revert("Decimals cannot be more than 21")

        total_supply = _initialSupply * 10 ** _decimals
        Logger.debug(f'on_install: total_supply={total_supply}', TAG)
        self._is_ice_age.set(False)
        self._total_supply.set(total_supply)
        self._decimals.set(_decimals)
        self._balances[self.msg.sender] = total_supply

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "ICONBET"

    @external(readonly=True)
    def symbol(self) -> str:
        return "ICBX"

    @external(readonly=True)
    def decimals(self) -> int:
        return self._decimals.get()

    @external(readonly=True)
    def totalSupply(self) -> int:
        return self._total_supply.get()

    @external(readonly=True)
    def is_iceage(self) -> bool:
        return self._is_ice_age.get()

    @external(readonly=True)
    def is_frozener(self, addr: Address) -> bool:
        return self._frozeners[addr]

    @external(readonly=True)
    def balanceOf(self, _owner: Address) -> int:
        return self._balances[_owner]

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        if( self._is_ice_age.get() ):
            revert("Stop all transfers")
        if _data is None:
            _data = b'None'
        if (self._frozeners[self.msg.sender]):
            revert("Frozen user")
        if (self._frozeners[_to]):
            revert("Frozen user")
        self._transfer(self.msg.sender, _to, _value, _data)

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        if _value < 0:
            revert("Transferring value cannot be less than zero")
        if self._balances[_from] < _value:
            revert("Out of balance")
        if self._balances[_to]+_value < self._balances[_to]:
            revert("balance overflow")

        self._balances[_from] = self._balances[_from] - _value
        self._balances[_to] = self._balances[_to] + _value

        if _to.is_contract:
            recipient_score = self.create_interface_score(_to, TokenFallbackInterface)
            recipient_score.tokenFallback(_from, _value, _data)

        self.Transfer(_from, _to, _value, _data)
        Logger.debug(f'Transfer({_from}, {_to}, {_value}, {_data})', TAG)
    
    @external
    def set_iceage(self, is_ok: bool) -> None:
        if not self.owner == self.msg.sender:
            self.revert('Only owner allowed.')
        self._is_ice_age.set(is_ok)
        Logger.debug(f'SetIceAge({is_ok})', TAG)
    
    @external
    def set_frozener(self, addr: Address, is_frozen:bool) -> None:
        if not self.owner == self.msg.sender:
            self.revert('Only owner allowed.')
        self._frozeners[addr] = is_frozen
        Logger.debug(f'SetFrozener({addr}, {is_frozen})', TAG)