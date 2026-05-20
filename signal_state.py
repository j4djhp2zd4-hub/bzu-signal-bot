"""
Signal State Manager
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict

logger = logging.getLogger(__name__)
STATE_FILE = "/tmp/signal_state.json"

class SignalState:
    def __init__(self, state_file: str = STATE_FILE, cooldown_minutes: int = 30):
        self.state_file = state_file
        self.cooldown_minutes = cooldown_minutes
    
    def _load_state(self) -> Dict:
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"last_signal": None, "last_signal_time": None}
    
    def _save_state(self, state: Dict):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except:
            pass
    
    def is_signal_allowed(self, signal: str) -> bool:
        state = self._load_state()
        last_signal = state.get("last_signal")
        last_time_str = state.get("last_signal_time")
        
        if not last_signal or not last_time_str:
            return True
        
        if last_signal != signal:
            return True
        
        try:
            last_time = datetime.fromisoformat(last_time_str)
            elapsed = (datetime.now(timezone.utc) - last_time).total_seconds() / 60
            return elapsed >= self.cooldown_minutes
        except:
            return True
    
    def record_signal(self, signal: str):
        state = self._load_state()
        state["last_signal"] = signal
        state["last_signal_time"] = datetime.now(timezone.utc).isoformat()
        self._save_state(state)