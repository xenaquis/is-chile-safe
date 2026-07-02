/**
 * jsonld.ts — Shared schema.org JSON-LD shape builders.
 *
 * Exports buildItemList + buildBreadcrumb producing schema.org-valid objects.
 * The rate is deliberately excluded from all ListItem shapes (resolved A1 —
 * schema.org ListItem has no honest rate slot; embedding it risks a
 * "safety leaderboard" reading, violating the editorial rule).
 *
 * Editorial rule enforced at build time: any provided list name must not
 * contain absolute safety terms (safest / most dangerous / safe / dangerous).
 * Violation throws at build time — the build fails, not the crawler.
 */

const BASE_URL = 'https://ischilesafe.com';

// ---------------------------------------------------------------------------
// Editorial guard — forbidden absolute safety terms
// ---------------------------------------------------------------------------
const FORBIDDEN = ['safest', 'most dangerous', 'safe', 'dangerous'];

function assertSafeName(name: string): void {
  const lower = name.toLowerCase();
  for (const term of FORBIDDEN) {
    if (lower.includes(term)) {
      throw new Error(
        `[jsonld.ts] Forbidden term "${term}" found in list name: "${name}". ` +
          `Use neutral phrasing such as "by reported CEAD incidence (ascending/descending)".`
      );
    }
  }
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ItemListRow = {
  name: string;
  slug?: string;
  url?: string;
};

export type ItemListOpts = {
  name?: string;
  order?: 'Ascending' | 'Descending' | 'Unordered';
  urlMode?: 'commune' | 'full';
};

export type BreadcrumbCrumb = {
  name: string;
  url?: string;
};

// ---------------------------------------------------------------------------
// buildItemList
// ---------------------------------------------------------------------------

/**
 * Build a schema.org ItemList object for a ranking table.
 *
 * - Rate is deliberately excluded (resolved A1).
 * - Editorial guard: opts.name must not contain forbidden absolute safety terms.
 * - urlMode 'commune' (default): url = BASE_URL + /commune/ or /es/comuna/ + slug + /
 * - urlMode 'full': each row must supply its own absolute url (for /rankings/ links to
 *   crime-type index pages, which are not /commune/ pages).
 * - order maps to schema.org ItemListOrder{Ascending|Descending|Unordered}.
 */
export function buildItemList(
  rows: ItemListRow[],
  locale: 'en' | 'es',
  opts?: ItemListOpts
): Record<string, unknown> {
  if (opts?.name) {
    assertSafeName(opts.name);
  }

  const urlMode = opts?.urlMode ?? 'commune';
  const prefix = locale === 'en' ? '/commune/' : '/es/comuna/';

  const itemListElement = rows.map((row, i) => {
    let url: string;
    if (urlMode === 'full') {
      if (!row.url) {
        throw new Error(
          `[jsonld.ts] buildItemList urlMode='full': row "${row.name}" must supply an absolute url.`
        );
      }
      url = row.url;
    } else {
      if (!row.slug) {
        throw new Error(
          `[jsonld.ts] buildItemList urlMode='commune': row "${row.name}" must supply a slug.`
        );
      }
      url = `${BASE_URL}${prefix}${row.slug}/`;
    }

    return {
      '@type': 'ListItem',
      position: i + 1,
      url,
      name: row.name,
    };
  });

  const orderMap: Record<string, string> = {
    Ascending: 'https://schema.org/ItemListOrderAscending',
    Descending: 'https://schema.org/ItemListOrderDescending',
    Unordered: 'https://schema.org/ItemListUnordered',
  };

  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    ...(opts?.name ? { name: opts.name } : {}),
    ...(opts?.order ? { itemListOrder: orderMap[opts.order] } : {}),
    numberOfItems: rows.length,
    itemListElement,
  };
}

// ---------------------------------------------------------------------------
// buildWebSite
// ---------------------------------------------------------------------------

/**
 * Build a schema.org WebSite object with a SearchAction for the site-level
 * sitelinks search box. Target points to the /map/ search parameter which
 * accepts free-text commune queries.
 */
export function buildWebSite(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'Chile Safety Map',
    url: BASE_URL,
    potentialAction: {
      '@type': 'SearchAction',
      target: `${BASE_URL}/map/?search={search_term_string}`,
      'query-input': 'required name=search_term_string',
    },
  };
}

// ---------------------------------------------------------------------------
// buildOrganization
// ---------------------------------------------------------------------------

/**
 * Build a schema.org Organization object for the site publisher.
 */
export function buildOrganization(): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Chile Safety Map',
    url: BASE_URL,
    description:
      'Interactive crime data map of Chile using official CEAD statistics.',
  };
}

// ---------------------------------------------------------------------------
// buildBreadcrumb
// ---------------------------------------------------------------------------

/**
 * Build a schema.org BreadcrumbList object.
 *
 * Crumbs without a url (typically the current/last page) emit ListItem
 * WITHOUT an `item` property — per schema.org BreadcrumbList spec.
 * Crumbs with a url emit `item` set to that absolute URL.
 */
export function buildBreadcrumb(crumbs: BreadcrumbCrumb[]): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: crumbs.map((c, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: c.name,
      ...(c.url ? { item: c.url } : {}),
    })),
  };
}
