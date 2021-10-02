# Root-Me Bot

This is a Discord bot to keep up with you progression on [Root-Me](https://www.root-me.org) :)

This project is heavily inspired by zTeeed's version of [RootMeBot](https://github.com/zteeed/RootMeBot)


## Building

You have to create a .env file in the `RootMeBot` folder to give your Root-Me API key, Discord API key, and Discord channel id the bot will use.
You can find a .env.example for the format.

Then, simply run the `run.sh` file.

## The project

This project fetches data from the [Root-Me API](https://api.www.root-me.org/) using `aiohttp`.
It uses `SQLAlchemy` to build and update the database about root-me challenges and followed users.
To post messages in Discord, the `discordpy` library is used.

The goal is to minimize concurrent connections to the Root-Me API to avoid getting banned by the rate-limiting.

