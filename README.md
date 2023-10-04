# MIND OF CEO, LUCAS BUBNER 2022
###### Mind is no longer being hosted due to Replit hosting changes.
# DESCRIPTION
'Mind of CEO' is a Flask application which is a text-based adventure game. This game is based on player input with selection boxes which will influence the next event that is displayed.
There are over 65 endings to the game, with all different and unique narrations and events caused by reaching these endings. The purpose of this project is to provide entertainment as a game.
Players can choose between a variety of options given a cirumstance, which will affect what options they are able to make in the future (for example, if a player had consumed an item, the option to
consume it later doesn't show as an option). The story is based on a CEO, and is from a perspective of a name that the player enters at the beginning. This perspective is also the username and personal experience systems implemented in this project.
After users return and provide a successful login, they are able to see an endings page where they can view the endings they've unlocked, while also being able to have more administrative action over their accounts such as delete, and seeing their savefile information. There are no reset/change password options, as this would need another verification method such as email in order to be effective. For the scope of this project, a change password option may cause security issues to some, and as such may be an ineffective idea.

# DESIGN CHOICES
In this project, I have decided to use an auto-save system with utilisation of the Python libraries Flask and Pickle. Savedata will automatically be saved to a file on a server filesystem, which will
hold data for a certain player. This allows for people to come back at another time and attempt to reach more endings. Originally, this system was not password protected, but I realise this is
not a great choice as people with conflicting names will have duplicate savefiles and can end up overriding each others saves. To combat this, all users have an Argon2 hashed password stored in an SQL database attached to their username, which is not for security of savefiles but for claiming a username.
A design problem that I recently encountered with this project is that user data would only load onto the one thread, and therefore this meant that if one person logged out, all users would log out. This would prove security and usability issues, and I have used a Flask session in order to combat this. This solution proves effective for this project, and has also utilised the pickle 'loads' and 'dumps' methods to serialise and deserialse the User save class.

# OPTIMISATIONS
With such a big project, certain optimisations are required in order to keep the code as little repetitive as possible. I have used the Jinja rendering and templating system to combat this, where I
have used a grand template followed by the custom additions in each HTML page. Using Flask routes, these were able to be easily programmed in, and able to follow logic through the User class system.
I have also tried to introduce security and information safety in this project, by checking each request for a valid savefile and username. If either of these do not exist, then they will be
redirected to the login screen. In addition, there are a few safety features in place for usernames, ones that involve not being able to manipulate file structures and also one to check if their username is within the 16 character limit I've imposed.

# FILES
*app.py*: Grand file which controls all the program operations, including app functions, app routes, and interfacing with the auth.db database<br>
*templates/*: Contains all the Flask templates and HTML files for rendering<br>
*static/*: Contains all assets including CSS files, JavaScript scripts to help the front-end work, and all images<br>
*savefiles/*: Filesystem storage for all savefiles that are created and used during the game<br>
*auth.db*: An SQL database that holds all the data for usernames and passwords, which is seperated from the savefiles. Passwords are hashed with argon2 and username salting.
