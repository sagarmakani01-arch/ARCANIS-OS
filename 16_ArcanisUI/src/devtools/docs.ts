export interface DocSection {
  id: string;
  title: string;
  content: string;
  type: 'guide' | 'api' | 'example' | 'tutorial';
  category: string;
  order: number;
  children?: DocSection[];
}

export interface DocSearchResult {
  section: DocSection;
  relevance: number;
  matchedContent: string;
}

export interface DocumentationSystem {
  addSection(section: DocSection): void;
  getSection(id: string): DocSection | undefined;
  getAllSections(): DocSection[];
  getSectionsByType(type: DocSection['type']): DocSection[];
  getSectionsByCategory(category: string): DocSection[];
  search(query: string): DocSearchResult[];
  generateMarkdown(): string;
  getTOC(): { id: string; title: string; level: number }[];
}

export function createDocumentation(): DocumentationSystem {
  const sections = new Map<string, DocSection>();

  function searchRecursive(section: DocSection, query: string): DocSearchResult[] {
    const results: DocSearchResult[] = [];
    const lowerQuery = query.toLowerCase();
    const lowerContent = section.content.toLowerCase();

    if (section.title.toLowerCase().includes(lowerQuery) || lowerContent.includes(lowerQuery)) {
      const titleMatch = section.title.toLowerCase().includes(lowerQuery);
      const contentIndex = lowerContent.indexOf(lowerQuery);
      const matchedContent = contentIndex >= 0
        ? section.content.substring(Math.max(0, contentIndex - 50), contentIndex + query.length + 50)
        : section.content.substring(0, 100);

      results.push({
        section,
        relevance: titleMatch ? 1.0 : 0.5,
        matchedContent,
      });
    }

    section.children?.forEach((child) => {
      results.push(...searchRecursive(child, query));
    });

    return results;
  }

  function toMarkdown(section: DocSection, indent = 0): string {
    const prefix = '#'.repeat(Math.min(indent + 1, 6));
    let md = `${prefix} ${section.title}\n\n${section.content}\n\n`;

    section.children?.forEach((child) => {
      md += toMarkdown(child, indent + 1);
    });

    return md;
  }

  function collectTOC(section: DocSection, results: { id: string; title: string; level: number }[], level = 0): void {
    results.push({ id: section.id, title: section.title, level });
    section.children?.forEach((child) => collectTOC(child, results, level + 1));
  }

  return {
    addSection(section) {
      sections.set(section.id, section);
    },
    getSection: (id) => sections.get(id),
    getAllSections: () => Array.from(sections.values()).sort((a, b) => a.order - b.order),
    getSectionsByType: (type) => Array.from(sections.values()).filter((s) => s.type === type),
    getSectionsByCategory: (category) => Array.from(sections.values()).filter((s) => s.category === category),
    search(query) {
      const results: DocSearchResult[] = [];
      sections.forEach((section) => {
        results.push(...searchRecursive(section, query));
      });
      return results.sort((a, b) => b.relevance - a.relevance);
    },
    generateMarkdown() {
      let md = '# ArcanisUI Documentation\n\n';
      Array.from(sections.values())
        .sort((a, b) => a.order - b.order)
        .forEach((section) => {
          md += toMarkdown(section) + '\n---\n\n';
        });
      return md;
    },
    getTOC() {
      const toc: { id: string; title: string; level: number }[] = [];
      Array.from(sections.values())
        .sort((a, b) => a.order - b.order)
        .forEach((section) => collectTOC(section, toc));
      return toc;
    },
  };
}
