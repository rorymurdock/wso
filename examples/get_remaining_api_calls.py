import wso

# Turn on debugging to see more info
UEM = wso.WSO(debug=True)

REMAINING = UEM.remaining_api_calls()
print("There are %i API calls remaining" % REMAINING)
