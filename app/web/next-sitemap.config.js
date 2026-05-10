/** @type {import('next-sitemap').IConfig} */

const config = {
  siteUrl: process.env.SITE_URL || 'http://localhost:3000',
  generateRobotsTxt: true,
  generateIndexSitemap: false,
  outDir: './public',
  exclude: [
    '/admin',
    '/api/*',
    '/jobs/[id]/private',
  ],
  robotsTxtOptions: {
    policies: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/admin', '/api'],
      },
    ],
    additionalSitemaps: [
      `${process.env.SITE_URL || 'http://localhost:3000'}/api/docs`,
    ],
  },
  changefreq: 'monthly',
  priority: 0.7,
  alternateRefs: [
    {
      href: `${process.env.SITE_URL || 'http://localhost:3000'}/en`,
      hreflang: 'en',
    },
  ],
};

module.exports = config;
