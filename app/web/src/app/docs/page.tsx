"use client";

import { useEffect, useState } from "react";

interface SitemapEntry {
  url: string;
  changefreq?: string;
  priority?: number;
  lastmod?: string;
}

interface ApiRoute {
  method: string;
  path: string;
  description: string;
  tags: string[];
}

interface OpenApiOperation {
  summary?: string;
  description?: string;
  tags?: string[];
}

type OpenApiPathItem = Record<string, OpenApiOperation>;

interface OpenApiSpec {
  paths?: Record<string, OpenApiPathItem>;
}

export default function DocsPage() {
  const [sitemapEntries, setSitemapEntries] = useState<SitemapEntry[]>([]);
  const [apiRoutes, setApiRoutes] = useState<ApiRoute[]>([]);
  const [activeTab, setActiveTab] = useState<"docs" | "sitemap">("docs");
  const [loading, setLoading] = useState(true);
  const docsUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/docs`;

  useEffect(() => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

    // Fetch sitemap entries
    const fetchSitemap = async () => {
      try {
        const response = await fetch("/sitemap.xml");
        if (response.ok) {
          const xml = await response.text();
          const parser = new DOMParser();
          const doc = parser.parseFromString(xml, "application/xml");
          const urls = Array.from(doc.querySelectorAll("url")).map((url) => {
            const loc = url.querySelector("loc")?.textContent || "";
            const changefreq =
              url.querySelector("changefreq")?.textContent || "monthly";
            const priority = parseFloat(
              url.querySelector("priority")?.textContent || "0.7",
            );
            const lastmod = url.querySelector("lastmod")?.textContent;

            return { url: loc, changefreq, priority, lastmod };
          });
          setSitemapEntries(urls);
        }
      } catch (error) {
        console.error("Failed to fetch sitemap:", error);
      }
    };

    // Fetch API routes from the OpenAPI spec
    const fetchApiRoutes = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/apispec.json`);
        if (response.ok) {
          const spec = (await response.json()) as OpenApiSpec;
          const routes: ApiRoute[] = [];

          for (const [path, methods] of Object.entries(spec.paths ?? {})) {
            for (const [method, operation] of Object.entries(
              methods as OpenApiPathItem,
            )) {
              if (method !== "parameters") {
                routes.push({
                  method: method.toUpperCase(),
                  path,
                  description:
                    operation.summary ||
                    operation.description ||
                    "No description",
                  tags: operation.tags || ["General"],
                });
              }
            }
          }

          setApiRoutes(routes);
        }
      } catch (error) {
        console.error("Failed to fetch API routes:", error);
      }
    };

    Promise.all([fetchSitemap(), fetchApiRoutes()]).finally(() => {
      setLoading(false);
    });
  }, []);

  const getMethodColor = (method: string) => {
    switch (method) {
      case "GET":
        return "bg-blue-100 text-blue-800";
      case "POST":
        return "bg-green-100 text-green-800";
      case "PUT":
        return "bg-yellow-100 text-yellow-800";
      case "DELETE":
        return "bg-red-100 text-red-800";
      case "PATCH":
        return "bg-purple-100 text-purple-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-4xl font-bold text-slate-900">Documentation</h1>
          <p className="text-slate-600 mt-2">API Documentation & Sitemap</p>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab("docs")}
              className={`py-4 px-2 font-medium text-sm border-b-2 transition-colors ${
                activeTab === "docs"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              API Docs
            </button>
            <button
              onClick={() => setActiveTab("sitemap")}
              className={`py-4 px-2 font-medium text-sm border-b-2 transition-colors ${
                activeTab === "sitemap"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              Sitemap ({sitemapEntries.length})
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="text-slate-600 mt-4">Loading documentation...</p>
          </div>
        ) : (
          <>
            {/* Docs Section */}
            {activeTab === "docs" && (
              <div className="space-y-6">
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-2xl font-bold text-slate-900 mb-4">
                    API Documentation
                  </h2>
                  <p className="text-slate-600 mb-6">
                    Open the API docs in a new tab to inspect the backend
                    routes and try them out.
                  </p>
                  <a
                    href={docsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Open docs page
                    <svg
                      className="w-4 h-4 ml-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                  </a>
                </div>

                {/* API Routes Overview */}
                <div className="bg-white rounded-lg shadow-md overflow-hidden">
                  <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
                    <h3 className="text-lg font-semibold text-slate-900">
                      Endpoints Overview
                    </h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-slate-50 border-b border-slate-200">
                        <tr>
                          <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                            Method
                          </th>
                          <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                            Path
                          </th>
                          <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                            Description
                          </th>
                          <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                            Tags
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        {apiRoutes.map((route, idx) => (
                          <tr
                            key={idx}
                            className="hover:bg-slate-50 transition-colors"
                          >
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span
                                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getMethodColor(route.method)}`}
                              >
                                {route.method}
                              </span>
                            </td>
                            <td className="px-6 py-4 font-mono text-sm text-slate-600 max-w-md overflow-x-auto">
                              {route.path}
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-600">
                              {route.description}
                            </td>
                            <td className="px-6 py-4 text-sm">
                              <div className="flex flex-wrap gap-2">
                                {route.tags.map((tag) => (
                                  <span
                                    key={tag}
                                    className="px-2 py-1 bg-slate-100 text-slate-700 text-xs rounded"
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Sitemap Section */}
            {activeTab === "sitemap" && (
              <div className="space-y-6">
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-2xl font-bold text-slate-900 mb-4">
                    Site Sitemap
                  </h2>
                  <p className="text-slate-600 mb-4">
                    Complete list of pages available on the Working Sundays
                    application. This sitemap is used for SEO and site
                    navigation.
                  </p>
                  <a
                    href="/sitemap.xml"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    View XML Sitemap
                    <svg
                      className="w-4 h-4 ml-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                  </a>
                </div>

                {/* Sitemap Entries */}
                {sitemapEntries.length > 0 ? (
                  <div className="bg-white rounded-lg shadow-md overflow-hidden">
                    <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
                      <h3 className="text-lg font-semibold text-slate-900">
                        Pages ({sitemapEntries.length})
                      </h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-slate-50 border-b border-slate-200">
                          <tr>
                            <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                              URL
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                              Priority
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                              Change Frequency
                            </th>
                            <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                              Last Modified
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                          {sitemapEntries.map((entry, idx) => (
                            <tr
                              key={idx}
                              className="hover:bg-slate-50 transition-colors"
                            >
                              <td className="px-6 py-4 text-sm">
                                <a
                                  href={entry.url}
                                  className="text-blue-600 hover:text-blue-800 hover:underline truncate block"
                                  title={entry.url}
                                >
                                  {entry.url.replace(
                                    /^https?:\/\/(.*?)\//,
                                    "/",
                                  )}
                                </a>
                              </td>
                              <td className="px-6 py-4 text-sm text-slate-600 text-center">
                                {entry.priority || 0.7}
                              </td>
                              <td className="px-6 py-4 text-sm text-slate-600 capitalize">
                                {entry.changefreq || "monthly"}
                              </td>
                              <td className="px-6 py-4 text-sm text-slate-600">
                                {entry.lastmod
                                  ? new Date(entry.lastmod).toLocaleDateString()
                                  : "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <p className="text-slate-600">
                      No sitemap entries found. Generate your project build to
                      create the sitemap.
                    </p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-slate-600 text-sm">
            <p>Working Sundays &copy; 2026. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
