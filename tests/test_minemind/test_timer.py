import time  
from datetime import datetime, timezone
 
class Timer(): 
    def __init__(self, created_dt=datetime.now(), saved_dt=None, elapsed_seconds=0.0, resumed_dt=datetime.now()): 
        self.created_dt = created_dt
        self.saved_dt = saved_dt 
        self.elapsed_seconds = elapsed_seconds
        self.resumed_dt = resumed_dt 
        self.timer = None  
    
    def get_created_dt(self): 
        return self.created_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_saved_dt(self): 
        return self.saved_dt.strftime("%Y-%m-%d %H:%M:%S") if self.saved_dt else None
    
    def get_resumed_dt(self): 
        return self.resumed_dt.strftime("%Y-%m-%d %H:%M:%S") if self.resumed_dt else None

    def start(self):
        if self.timer is None:  
            self.timer = time.perf_counter()  
            # print(f"Timer started: {self.get_resumed_dt()}, Elapsed time: {(self.get_elapsed_seconds_hms())}", )
            return True  
        return False 

    def resume(self) -> None: 
        if self.timer is None:  
            self.timer = time.perf_counter() 
            self.resumed_dt = datetime.now()  
            # print(f"Timer resumed: {self.get_resumed_dt()}, Elapsed time: {self.get_elapsed_seconds_hms}", )
            return True  
        return False  

    def stop(self) -> None: 
        if self.timer is None:
            return 
        now = time.perf_counter() 
        self.elapsed_seconds += max(0.0, now - self.timer)
        self.timer = None

    def get_elapsed_seconds(self): 
        base = self.elapsed_seconds
        if self.timer is not None:  
            now = time.perf_counter()
            base += max(0.0, now - self.timer)
        return base

    def get_elapsed_seconds_hms(self): 
        sec = int(self.get_elapsed_seconds())
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
  
    def ts_to_iso(ts: float):
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    def iso_to_ts(s: str):
        # robust enough for your use
        return datetime.fromisoformat(s).timestamp()