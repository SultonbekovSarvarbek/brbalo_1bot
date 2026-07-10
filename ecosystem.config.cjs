module.exports = {
  apps: [
    {
      name: "brbalo-instagram-bot",
      cwd: __dirname,
      script: "main.py",
      interpreter: "./.venv/bin/python",
      autorestart: true,
      watch: false,
      restart_delay: 5000,
      max_restarts: 10,
      kill_timeout: 10000,
      time: true,
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
