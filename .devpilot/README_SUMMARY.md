# Project Structure

This project is structured as follows:

## Key Files and Relationships

1. **[root directory]**
    - `tailwind.config.js`: Configuration file for Tailwind CSS.
    - `vite.config.js`: Vite configuration file.
    - `eslint.config.js`: ESLint configuration file.
    - `postcss.config.js`: PostCSS configuration file.
    - **src/** (Source directory)
        - `main.jsx`: Entry point of the application.
        - `App.jsx`: Main component for rendering the entire app.
        - **components/** (Components directory)
            - `Button_Score.jsx`: Custom Button for displaying scores.
            - `Button_x_o.jsx`: Custom Button for X and O in the game.
            - `Announcement_Modal.jsx`: Modal for announcing the winner or a draw.
            - `Button_Game.jsx`: Custom Button to start a new game.
            - `Restart_Modal.jsx`: Modal for restarting the current game.
        - **pages/** (Pages directory)
            - `Main_Page.jsx`: Page for the main application interface.
            - `Game_Page.jsx`: Page dedicated to the game itself.

This project uses Vite as a build tool, Tailwind CSS for styling, and ESLint for linting. PostCSS is also used in conjunction with Tailwind for customizations.