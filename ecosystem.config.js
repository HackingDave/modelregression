module.exports = {
  apps: [
    {
      name: "modelregression",
      script: "node_modules/.bin/next",
      args: "start -p 3002",

      node_args: [
        "--max-old-space-size=512",
        "--optimize-for-size",
        "--gc-interval=100",
      ],

      env: {
        NODE_ENV: "production",
        PORT: 3002,
      },

      max_memory_restart: "400M",
      kill_timeout: 10000,
      wait_ready: false,
      listen_timeout: 30000,

      instances: 1,
      exec_mode: "fork",

      autorestart: true,
      max_restarts: 10,
      min_uptime: 10000,

      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      error_file: "/var/log/pm2/modelregression-error.log",
      out_file: "/var/log/pm2/modelregression-out.log",
      combine_logs: true,
      merge_logs: true,

      cron_restart: "0 4 * * *",

      watch: false,
      ignore_watch: ["node_modules", ".next", "public", "benchmark"],
    },
  ],
};
