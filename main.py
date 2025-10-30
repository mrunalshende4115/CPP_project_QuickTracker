from quicktrack4115.checkin import check_in
from quicktrack4115.checkout import check_out
from quicktrack_utils.vehicle import batch_register
from quicktrack_utils.db import update_status
from quicktrack_utils.logger import log_event
from quicktrack_utils.alerts import send_sns_alert

batch_register("sample_data/vehicles.json")

data = check_in("V001", "Dublin Depot")
update_status(**data)
log_event(f"Checked in: {data}")
send_sns_alert("V001", "Checked in successfully")

data = check_out("V001", "City Center")
update_status(**data)
log_event(f"Checked out: {data}")
send_sns_alert("V001", "Checked out successfully")