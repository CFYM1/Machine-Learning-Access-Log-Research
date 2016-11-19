#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)
# install package e1071, if not installed yet
# install.packages("e1071")
# Load the package "e1071"
library(e1071)

# test the arguments: return an error if necessary
if (length(args)==1) {
  if (args[1]=="-h") {
    message("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n\n
Command Line Arguments
	-s : Sharing Value (Default value: 0.5)
	-S : Seed value (Default value: 123)
	-h : Print help\n\n
Description
	This R script trains and tests a naive bayes model.
	At least one argument is mandatory (-h or CSV file)\n
	The CSV file must be generated using the Python script Scalper, or it must have the following headers:\n
	| Host | Log_Name | Remote_User | Date_Time | Method | URL | Response_Code | Bytes_Sent | Referer | User_Agent | PASS |\n
	The PASS column must be filled, in order to be able to compute the test.The separator used must be ','.\n
	The sharing value is a numeric value between 0 and 1. It sets the data distribution from the csv file to the train set.
	Example: If the sharing value equals 0.67, 67% of the data entries will go to the train set, and the rest will go to the test set.\n
	The seed value is used to generate a random number, which will be used to shuffle the data entries before computing the train set and the test set.
	An identical seed value will induce the same shuffling.\n")
    quit()
  } else if(grepl('.csv$', args[1])) {
    seed <- 123
    sharing <- 0.5
    message("Default sharing value: ", sharing)
    message("Default seed value: ", seed)
  } else {
    stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n", call.=FALSE)
  }
} else if(length(args)==3) {
  if(grepl(".csv$", args[1])==F) {
    stop("IUsage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n", call.=FALSE)
  }
  if(args[2]!="-s" && args[2]!="-S") {
    stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n", call.=FALSE)
  }
  if(args[2]=="-s") {
    buffer <- as.double(args[3])
    if(is.na(buffer) || buffer <= 0 || buffer >= 1){
      stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n\nSharing value must be between 0 and 1 strictly\n", call.=FALSE)
    } else {
      sharing <- buffer
      seed <- 123
    }
  } else if(args[2]=="-S") {
    buffer <- as.double(args[3])
    if(is.na(buffer)){
      stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n\nSeed value must be an integer\n", call.=FALSE)
    } else {
      seed <- args[3]
      sharing <- 0.5
    }
  }
  message("Sharing value: ", sharing)
  message("Seed Value: ", seed)
} else if(length(args)==5) {
  if(grepl(".csv$", args[1])==F) {
    stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n", call.=FALSE)
  }
  if((args[2]!="-s" && args[2]!="-S") || (args[4]!="-s" && args[4]!="-S") || (args[2]==args[4])) {
    stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n", call.=FALSE)
  }
  buffer1 <- as.double(args[3])
  buffer2 <- as.double(args[5])
  if(args[2]=="-s") {
    if(is.na(buffer1) || buffer1 <= 0 || buffer1 >= 1){
      stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n\nSharing value must be between 0 and 1 strictly\n", call.=FALSE)
    } else {
      sharing <- buffer1
    }
  } else if(args[4]=="-s") {
    if(is.na(buffer2) || buffer2 <= 0 || buffer2 >= 1){
      stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n\nSharing value must be between 0 and 1 strictly\n", call.=FALSE)
    } else {
      sharing <- buffer2
    }
  }
  if(args[2]=="-S") {
    if(is.na(buffer1)){
      stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n\nSeed value must be an integer\n", call.=FALSE)
    } else {
      seed <- args[3]
    }
  } else if(args[4]=="-S") {
    if(is.na(buffer2)){
      stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n\nSeed value must be an integer\n", call.=FALSE)
    } else {
      seed <- args[5]
    }
  }
  message("Sharing value: ", sharing)
  message("Seed Value: ", seed)
} else {
  stop("Usage: Rscript classifier.R [-h] [file.csv] [-s VALUE] [-S VALUE]\n", call.=FALSE)
}

dataset <- read.csv(args[1], header = T, sep = ",")

## Get the number of input dataset
num.dataset <- nrow(dataset)

## Set the number of training dataset = 2/3 of all dataset
num.train <- round(sharing * num.dataset)

## Set the number of test dataset = 1/3 of all dataset
num.test <- num.dataset - num.train

## Randomly split dataset into training and test data
## To be able to reconstruct this experiment.
set.seed(seed)
s <- sample(num.dataset) 

### Get the training set
## First, generate indices of training dataset
indices.train <- s[1:num.train]

## Second, get the training dataset
train <- dataset[indices.train,]

### Get the test set 
indices.test <- s[(num.train+1):num.dataset]
test <- dataset[indices.test,]

message("\n\n#####  MODEL USING ALL FEATURES #####")

# to create a Naive Bayes model
M1 <- naiveBayes(PASS ~ ., data=train)

# prediction on test data
message("\nPrediction on test data -- M1")
ptm <- proc.time()
P1 <- predict(M1, test[1:10], type="class")
print(proc.time() - ptm)

message("\nDistribution of the predicted values -- M1")
print(table(P1))

## RESULT

message("\nComparing the predicted values with the true values -- M1")
print(table(test$PASS, P1))

## RESULT

message("\nPercentage of the correctly predicted values on the test set = ", 
        round(sum(diag(table(test$PASS, P1)))/num.test * 100, 2), "%"
)
