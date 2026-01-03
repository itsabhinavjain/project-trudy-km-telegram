## TODO 
- Redefinition of the requirements (Abhinav, manually)
  - Define the PRD 
  - File structure and the name of the various files 
  - Usage 
    - How should setup happen
    - While creating the script - What are the various flags and functionality 
    - What sequence should the script run as 
    - How will cleanup be managed 
  - Setup script 
  - What all types of messages can be supported (Check documentation for that)
  - What all post processing should be done for the various type of messages 
    - What should the output file look like? 
    - What can be the error conditions and edge cases and how should they be handled? 
  - Build a pipeline instead of having a single file. There should be a staging area to save the files. 
    - Command for updating users 
    - Command for fetching the messages and the media 
    - Commond for L1 processing of messages 
  - What are the various flags in the tool 

## Backlog (Potential improvements - Not to be implemented right now)

- Later can add slash commands in the bot to send various kinds of messages 
  - The slash commands can be used to tag the various type of notes 
  - The slash commands can be used to ask 

- Trudy can also proactively send messages back to the user on what he has done. This should be ignored while downloadin

- More scripts can be added to post post process these notes and generate insights. 
  - These insights can be used to generate reports and develop audiences. 

- Can probably make a skill out of this later 
  - Need to specific the environment variables 
  - Where to call the script from 
  - What all dependencies to be added to pyproject.toml
  - Where should you have the pyproject.toml file?
  - The uv tools should use actual filename instead of aliases 
  - Need to define a workspace 
    - Where the output is to be saved (data)
    - Where to save the config 
  - Where to save the run logs etc 
  - SKILLS.md file

(Move this to the overall vision of trudy in other repository)