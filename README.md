# *Mind* of CEO

## Overview
- Flask-based text adventure game
- Player choices dynamically affect story progression
- 65+ unique endings with distinct narratives
- Single-player, text-driven experience

## Gameplay
- Choice-based selection boxes determine future options
- Actions persist (e.g. consumed items are removed from later choices)
- Story told from the perspective of a CEO
- Player-entered name for multiple functions
  - Username
  - Narrative identity
  - Savefile owner
- Automatic saving of progress
- Returning user support to
  - Log in
  - View unlocked endings
  - View save data
  - Delete their account

>[!NOTE]
>Password reset/change is not implemented due to scope and lack of user verification.

## Technical
- Backend built with Flask (Python)
- Automatic save system using `pickle` and filesystem storage
- SQL database for usernames and passwords
- Passwords hashed with `argon2`
- Authentication used to prevent username/save collisions
- Flask sessions used to isolate user state
- Fixes cross-user logout and threading issues
- User data serialized with `pickle`

## Optimisations
- Jinja templating with a shared base layout
- Minimal HTML repetition across pages
- Flask routes integrated with User logic
- Validation for usernames and savefiles
- Username safety checks
  - Maximum length of 16 characters
  - Filesystem manipulation prevention

###### Lucas Bubner, 2022