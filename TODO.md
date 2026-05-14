# todo


Result presentation and evaluation
Automatization script which talks directly to the api with .job files used for hyperparam optimization



# done
Implement radius_km calculation flow based on whatever metrics
Manage jar execution and log forwarding to the client

Make dockerfile for everything (figure out deployment)
later
add authenticated users to each server, need database for this, db can be shared fuck it
Settings tab is ready without saving the stores or anything (provide the user with option to save or discard if they try to proceed without saving)
Job import/export is not clear, the button does not allow for import of .job files only of .json files, which is incorrect. Exported .job file should have all the stores contained within it for easy reconstruction, not require the stores to be uploaded afterwards.
Implement frontend to use this api, to define this on paper aswell
fix bug of logs not being remembered (add log file for each job and read from it to have live logs)