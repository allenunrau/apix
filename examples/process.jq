# jq filter to extract and transform API response data
# Applied to the JSON output from the endpoints module

# Extract just the id, name, and email from the first endpoint result's data
.[0].data | .[] | {id, name, email, username}