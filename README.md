# Packmaster Metrics
This repository contains the scripts that I use to generate insights into the metric data from 
[Packmaster](https://github.com/erasels/PackmasterCharacter) character runs.  
  
As of the 22nd of September 2023 we had a little over 139k run metrics collected so there are some interesting conclusions 
to be drawn once the information is properly sanitized and evaluated. The insights are currently available in [this discord thread](https://discord.com/channels/309399445785673728/1154170413472022579).  
  
To set this up yourself, you will need to download the [metrics](https://mega.nz/file/RR9hmJDY#v4g8eOTu8qU6zrWRMGa8E22kO-cFgMmV1H-hkqlROgo)
and create a metrics directory in the data directory where you should unzip them.  
After that, simply call the insights you wish to generate at the end of the main.py script.  
  
If you wish to only access data within a certain timeframe, use the ``round_date_keys`` on the `date_to_metrics` dictionary
and specify the level of rounding you need. For example, if you want all metrics grouped by year, you would use level 1 
which then returns a dictionary with a key for each year which is associated with a list of all metrics within that year.
