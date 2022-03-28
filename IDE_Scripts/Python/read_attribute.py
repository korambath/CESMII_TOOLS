#
# This scripts read attribute values and print it.
#
from datetime import datetime, timedelta
import pytz
import pandas as pd
from thinkiq import database
from thinkiq.model.equipment import Equipment

def load_value_stream_fast(self, start_time, end_time,max_samples=0):
    sql_command = "SELECT hist.ts AS timestamp, hist.status, hist.intvalue, hist.boolvalue, hist.floatvalue, hist.stringvalue, hist.datetimevalue, hist.intervalvalue, hist.data_type \
                FROM history.get_raw_history_data_with_sampling(ARRAY[{}::BIGINT], '{}', '{}', '{}') AS hist ORDER BY hist.ts ASC;".format(
        str(self.id), str(start_time), str(end_time),str(max_samples))
    with database.connect() as conn:
        with conn.cursor() as cur:
            try:
                df = pd.read_sql(sql_command, conn)
            except Exception as msg:
                #print('sql error: ', msg)
                return None
    df.drop(columns=['datetimevalue', 'intervalvalue', 'data_type'],inplace=True)
    if self.data_type == 'float':
        df['value']=df['floatvalue']
    elif self.data_type == 'int':
        df['value'] = df['intvalue']
    elif self.data_type == 'bool':
        df['value'] = df['boolvalue']
    elif self.data_type == 'string':
        df['value'] = df['boolvalue']

    df.drop(columns=['floatvalue','intvalue', 'boolvalue', 'stringvalue'], inplace=True)

    if df is None:
        self.value_stream = ValueStream()
    else:
        vsdf = df
        vsdf.set_index("timestamp", inplace=True)

    if max_samples > 0 and vsdf.shape[0]>2:
        reindex = pd.date_range(start=start_time, end=end_time, periods=max_samples, tz="UTC")
        vsdf=vsdf.reindex(reindex, method='ffill')

    return vsdf

#
# a minimalist script sample to read attribure and print
#
from thinkiq_context import get_context    
context = get_context()                         # the context object holds runtime information such as the equipment id and data stored between runs
equipment_id = context.std_inputs.node_id       # the id of the equipment instance to use
print(f'Equipment id is {equipment_id}')
print(context.std_inputs.parent_id)
eqpt = Equipment.get_from_id(equipment_id)      # creates an object for this equipment item
print(f'Running script {context.std_inputs.script_name} on {eqpt.display_name}')
context.logger.info(f'Running script {context.std_inputs.script_name} on {eqpt.display_name}')   # shows how to use the context object and equipment model
attr = eqpt.get_attribute("temperature_ppk1")
start_time = datetime(2021,12,20,0,0,0,0,pytz.UTC)
end_time = datetime(2022,1,9,0,0,0,0,pytz.UTC)
vts = load_value_stream_fast(attr, start_time, end_time)

print ("Return the output")
print(vts)
