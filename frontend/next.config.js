const isDev = process.env.NODE_ENV !== 'production';
const dest = isDev
  ? 'http://localhost:8000'
  : 'https://clone-api.fly.dev';

module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${dest}/:path*`,
      },
    ];
  },
};
