## FullStackDeveloper Nanodegree- Multi User Blog

In this project we are  building a multi user blog where users can sign in and post blog posts as well as 'Like' and 'Comment' on other posts made on the blog.

#Use the following urls:

/blog - for front page of blog

/blog/newpost - for adding new post to the blog

/blog/post([0-9]+) - to visit post page

#Directory Structure
1. static -contains all the CSS,JS files
2. templates -contains all the template(.html) files
3. app.yaml
4. main.py
5. models.py
6. README.md

#Follow the steps below to run the app :

1. Download Google App Engine Console
 
2. Clone the repository from https://github.com/ghoshabhi/Multi-User-Blog.git
 
3. To run locally :
       - Unzip the contents from the cloned directory and find the file "app.yaml".
        
       - Navigate to the location where the repo was cloned.
        
       - Run the command dev_appserver.py .
       
       - Now open localhost:8080 in browser
4. If you want to visit the live hosted app, visit this URL : https://basic-blog-149819.appspot.com
 
#Resources
 
1. Python is used as the scripting language for the server
    
2. jinja2, a templating library.
    
3. ndb : The Google Datastore NDB Client Library allows App Engine Python apps to connect to Cloud Datastore.

4. re to enable Regular Expression check for email and password inputs

5. App Engine : Google App Engine (GAE), Google's platform as a service solution.




