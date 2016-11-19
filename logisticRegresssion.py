from sklearn import cross_validation
from scalper import scalper
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn import metrics
import sys
import time

def specificity(y,y_hat):
    mc = metrics.confusion_matrix(y,y_hat)
    res = mc[0,0]/np.sum(mc[0, :])
    return res


def logisticRegression(data):
    print ""
    print "==============LOGISTIC REGRESSION=================="
    df = pd.DataFrame(data)

    matrix = df.as_matrix()


    start = time.time()
    X = matrix[:,1:5]
    y = matrix[:,0]


    X_app, X_test, y_app, y_test = cross_validation.train_test_split(X, y,test_size=int(len(data)/3),random_state= 0)
    print ""
    print "Learning set size: %d requests" % X_app.shape[0]
    print "Test set size: %d requests" % X_test.shape[0]
    print ""

    lr = LogisticRegression()

    modele = lr.fit(X_app,y_app)

    print "   User-Agent Size    HTTP Method        URL Size       Response Bytes    Intercept"
    print modele.coef_, modele.intercept_
    print ""


    y_pred = modele.predict(X_test)


    cm = metrics.confusion_matrix(y_test,y_pred)
    print "Confusion matrix: "
    print "                |    Predicted    |"
    print " _______________|   KO   |   OK   |"
    print "   Actual  | KO |  ",cm[0][0],"   | ",cm[0][1],"  |"
    print " __________| OK |  ",cm[1][0],"   | ",cm[1][1]," |"
    print ""

    acc = metrics.accuracy_score(y_test,y_pred)
    print "Accuracy: ", acc

    err = 1.0 - acc
    print "Error: ", err

    specificite = metrics.make_scorer(specificity, greater_is_better=True)
    sp = specificite(modele,X_test,y_test)
    print "Specificity: ", sp
    tt = time.time() - start
    print "Time:",tt

    print ""
    print "==============CROSS VALIDATION=================="

    success = cross_validation.cross_val_score(lr,X,y,cv=10,scoring='accuracy')

    print "Success: ",success
    print "Mean Success: ", success.mean()
    tt = time.time() - start
    print ""
    print "Processed in %f s" % (tt)



def help():
    print("Logistic Regression for the apache log by FCYM - https://github.com/FCYM")
    print("usage:  ./logisticRegression.py [log_file] [filter_file] [blacklist_database.txt] ")


def main(argc, argv):
    if argc < 4 or argv[1] == "--help":
        help()
        sys.exit(0)
    else:
        for i in range(argc):
            filters = argv[2]
            access = argv[1]
            blacklistIPPath = argv[3]

    data = scalper(access, filters,blacklistIPPath, False)
    methods = ["POST", "GET", "OPTIONS", "HEAD", "DELETE", "TRACE", "PUT", "CONNECT"]
    newData = []
    for d in data:
        rbytes = 0
        method_int = 0
        if(d['response_bytes'] != '-'):
            rbytes = d['response_bytes']
        if d['request_method'] in methods:
            method_int = methods.index(d['request_method'])
        else:
            method_int = len(methods)

        newData.append({'pass': d['pass'], 'response_bytes': int(rbytes), 'request_url_len': len( d['request_url']), 'request_header_user_agent_len': len(d['request_header_user_agent']), 'request_method_int': method_int})

    np.random.shuffle(newData)
    logisticRegression(newData)


if __name__ == "__main__":
    main(len(sys.argv), sys.argv)

