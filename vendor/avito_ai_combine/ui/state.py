from dataclasses import dataclass
@dataclass
class AppState:
    account_name:str='Not connected'; api_state:str='offline'; webhook_state:str='offline'; sync_state:str='idle'; autonomy_mode:str='COPILOT'; pending_approvals:int=0
