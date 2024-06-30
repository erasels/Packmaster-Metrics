# Packmaster Metrics
This repository contains the scripts that I use to generate insights into the metric data from 
[Packmaster](https://github.com/erasels/PackmasterCharacter) character runs.  
  
As of the 29th of June 2024 we have a little over 800k run metrics collected so there are some interesting conclusions 
to be drawn once the information is properly sanitized and evaluated. The main point of conversation around these insights happens in [this discord thread](https://discord.com/channels/309399445785673728/1154170413472022579).  
  
I upload the data into a google sheet that allows for easy exploration, found [here](https://docs.google.com/spreadsheets/d/146GPNf1aCHj5URk_oMkYS064HuRcP4vgbtCAkQ9NVWo/edit?gid=101337378#gid=101337378)
  
To set this up yourself, you will need to download the [metrics1](https://mega.nz/file/NREESLaK#fcboEgpDb-LF9jtDysycK7VrfwEKB3T0AZILFSbmADs) & [metrics2](https://mega.nz/file/RV1jAJCS#sKc_qmY_qH3zLqb1urrpfiUEf-bQadRn95b64lKn6SQ)
and create a metrics directory in the data directory where you should unzip them.  
After that, simply call the insights you wish to generate at the end of the main.py script.  

To print or write a human-readable table to file, use the helper methods provided in the results script.  
They turn the return of any of the insight methods into something that's easy to parse.
      
If you wish to only access data within a certain timeframe, use the ``round_date_keys`` on the `date_to_metrics` dictionary
and specify the level of rounding you need. For example, if you want all metrics grouped by year, you would use level 1 
which then returns a dictionary with a key for each year which is associated with a list of all metrics within that year.
