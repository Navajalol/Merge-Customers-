# Customer list merge

Merges two messy customer CSVs into one clean list: no duplicate customers,
normalized emails and phone numbers, dates in `YYYY-MM-DD`, and the earlier
signup date kept when a customer is in both files.

I am able to do this by grouping all the rows that have the same phone number/email 
and collapsing them into one row for both CSVs. I normalize the data before grouping 
the users by making each data be the same format.

## Run it

```bash
python merge_customers.py data/team_a.csv data/team_b.csv -o merged.csv
```
The merged CSV goes to `merged.csv`. A summary and any flagged rows are printed
to stderr, so nothing is changed silently.


## What I would do different 

I would want to make it more scalable, as it is now it does not have much room to be scaled to big CSVs 
that contain hundreds of thousands of lines without it taking a very long time and resources. Another algorithm 
I would use would be the Union-find algorithm to group the rows for the users. With that algorithm I would be able
to scale up the application to be able to use CSVs with millions of lines. 
I would also want to be more strict with the dates, email, and phone groupings. For example for the dates I had to assume 
if the data I was given was day first or month first when they were both below 12, with longer time I would try to find a more 
efficient way to get the date easier. I could also have used an actual list of all phone numbers and find if the phone number is 
real or not. With that I would have been able to flag possible users as not real. I could have also put all of the new data 
not into a CSV but into a data warehouse/database to be able to easily query from, such as in snowflake/databricks. 


