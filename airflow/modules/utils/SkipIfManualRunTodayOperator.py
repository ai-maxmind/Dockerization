from airflow.models import BaseOperator, DagRun
from airflow.utils.decorators import apply_defaults
from datetime import datetime
import pytz

class SkipIfManualRunTodayOperator(BaseOperator): 
    @apply_defaults
    def __init__(self, timezone="Asia/Ho_Chi_Minh", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timezone = pytz.timezone(timezone)

    def execute(self, context):
        session = context["session"]
        dag = context["dag"]

        today = datetime.now(self.timezone).date()
        startOfDay = datetime(today.year, today.month, today.day, tzinfo=self.timezone)

        runsToday = (
            session.query(DagRun)
            .filter(
                DagRun.dag_id == dag.dag_id,
                DagRun.execution_date >= startOfDay,
            )
            .all()
        )

        for run in runsToday:
            if run.run_type == "manual" and run.state == "success":
                self.log.info(
                    f"⚠️ DAG '{dag.dag_id}' đã được chạy thủ công thành công lúc {run.execution_date}. "
                    f"Bỏ qua run tự động trong ngày {today}."
                )
        return True
