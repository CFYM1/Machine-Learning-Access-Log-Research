# Machine-Learning-Access-Log-Research
Machine Learning scrips in python and R on apache access_log

#scalper.py


###Description
Scaper is a script based on apache-scalp that parses a combined common log format of access_log file from Apache. It checks some of the of requests are suspicious or not. It returns either a .csv file or a list of the request with an addtional key named 'pass' that is either 'OK' or 'KO' that can be reused in other programs.

###Usage:
```
$ python scalper.py [access_log] [default_filters.xml] [full_blacklist_databse.txt]
```

#classifier.R


###Usage: 

```
Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]
```

Command Line Arguments
	-s : Sharing Value (Default value: 0.5)
	-S : Seed value (Default value: 123)
	-h : Print help

Description
#

This R script trains and tests a naive bayes model.
At least one argument is mandatory (-h or CSV file)
	
The CSV file must be generated using the Python script Scalper, or it must have the following headers:
	| Host | Log_Name | Remote_User | Date_Time | Method | URL | Response_Code | Bytes_Sent | Referer | User_Agent | PASS |

The PASS column must be filled, in order to be able to compute the test. The separator used must be ','.

The sharing value is a numeric value between 0 and 1. It sets the data distribution from the csv file to the train set.
Example: If the sharing value equals 0.67, 67% of the data entries will go to the train set, and the rest will go to the test set.

The seed value is used to generate a random number, which will be used to shuffle the data entries before computing the train set and the test set.
An identical seed value will induce the same shuffling. 

	
MANDATORY: The "e1071" package for R must be installed

Method 1: Install from source

Download the add-on R package e1071 and type the following command in Unix console to install it to /my/own/R-packages/:
```
$ R CMD INSTALL e1071 -l /my/own/R-packages/
```
Method 2: Install from CRAN directly

Type the following command in R console to install it to /my/own/R-packages/ directly from CRAN:
```
> install.packages("e1071", lib="/my/own/R-packages/")
```
