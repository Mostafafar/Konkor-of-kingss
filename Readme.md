# Telegram Quiz Bot

A Telegram bot that allows students to add multiple-choice questions and answers to a database, with creative features.

## Features

- Students can add multiple-choice questions with 4 options
- Stores questions in a SQLite database
- Supports categories and difficulty levels
- Random quiz functionality
- User statistics tracking
- Explanation field for each question
- Interactive conversation flow for adding questions

## Setup

1. Clone this repository
2. Install requirements: `pip install -r requirements.txt`
3. Create a `config.py` file with your bot token
4. Run the bot: `python bot.py`

## Commands

- `/start` - Start the bot
- `/help` - Show help
- `/add_question` - Add a new question
- `/quiz` - Get a random question
- `/stats` - Show your statistics
- `/categories` - List available categories

## Database Schema

The bot uses SQLite with the following tables:

- `users` - Stores user information
- `questions` - Stores all questions
- `user_stats` - Tracks user activity and contributions