/**
 * Mindmap Parser Tests
 * 
 * Tests for:
 * 1. Single root node guarantee
 * 2. Table markdown handling
 * 3. Source marker extraction
 * 4. Heading hierarchy correctness
 */

import { parseMarkdownToMindmap } from '../mindmap-parser';

// Test markdown with table (from user's example)
const MARKDOWN_WITH_TABLE = `- 提取最佳短句、共鸣观点、原创框架
### 从零开始
- 收藏让你停止滑动的帖子
- 收集改变你思维的段落（Newsletter、书籍）
- 通过接触建立品味博物馆 [TIME:20:20]
- 规律自然浮现于创作中 [TIME:20:52]
## 输出量的误区 [TIME:22:23]
- 发布频率 ≠ 成功（Gary V/Alex Hormozi 简化论）
- 更多内容 = 更多噪音，非更多机会 [TIME:26:10]
- **想法质量 > 输出频率** [TIME:23:00]
- 精细制作救不了差想法 [TIME:23:15]
- 价值在细节，非简化 [TIME:25:15]
- 原始、冗长、简朴的内容成为 AI 时代的竞争优势 [TIME:25:52]
## 构建你的独特信号 [TIME:26:46]
- **信号** = 你因特定路径与使命而关注到的观点
- AI 无法制造信号（缺乏亲身经历与真实使命）[TIME:27:28]
- 特定目标决定你的注意力优先级 [TIME:28:06]
## 使命型 vs 话题型定位 [TIME:28:30]
| 类型 | 定义 | 优缺点 |
|------|------|--------|
| **话题型** | 选定细分 → 做专家 | 易被复制；限制学习与转型 |
| **使命型** | 推动转变 → 任何相关内容 | 允许演进；可持续性强 [TIME:29:07] |
## 核心要点
- 发展**个人视角**，思考而非套用模板 [TIME:08:24]
- 创作你想看到的内容 [TIME:12:20]
- 做导演而非执行者 [TIME:20:17]
- 持续性 > 高频率 [TIME:22:47]
- **你的路径 + 使命 = 唯一对抗 AI 的优势** [TIME:27:59]`;

// Test markdown with proper root heading
const MARKDOWN_WITH_ROOT = `# 内容创作策略
## 输出量的误区
- 发布频率 ≠ 成功
- 更多内容 = 更多噪音
## 构建你的独特信号
- 信号 = 你因特定路径与使命而关注到的观点`;

// Test markdown with multiple top-level headings
const MARKDOWN_MULTIPLE_ROOTS = `# 第一个主题
- 内容1
# 第二个主题
- 内容2
# 第三个主题
- 内容3`;

// Test markdown with source markers
const MARKDOWN_WITH_MARKERS = `# 视频笔记
- 重要观点 [TIME:12:30]
- 另一个观点 [TIME:1:23:45]
- 文档引用 [PAGE:15]
- 多页引用 [Page 20-25]`;

describe('Mindmap Parser', () => {
  describe('Single Root Node Guarantee', () => {
    it('should create exactly one root node for markdown with proper heading', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_ROOT);
      const rootNodes = result.nodes.filter(n => n.depth === 0 && !n.parentId);
      
      expect(rootNodes.length).toBe(1);
      expect(rootNodes[0].content).toContain('内容创作策略');
    });

    it('should handle markdown without root heading by creating default root', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_TABLE);
      const rootNodes = result.nodes.filter(n => n.depth === 0 && !n.parentId);
      
      // Should have exactly one root node
      expect(rootNodes.length).toBe(1);
    });

    it('should handle multiple top-level headings by keeping only first as root', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_MULTIPLE_ROOTS);
      const rootNodes = result.nodes.filter(n => n.depth === 0 && !n.parentId);
      
      // Should have exactly one root node
      expect(rootNodes.length).toBe(1);
      expect(rootNodes[0].content).toContain('第一个主题');
    });

    it('should ensure all non-root nodes have a parentId', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_ROOT);
      const nonRootNodes = result.nodes.filter(n => n.depth > 0);
      
      nonRootNodes.forEach(node => {
        expect(node.parentId).toBeDefined();
        expect(node.parentId).not.toBe('');
      });
    });
  });

  describe('Table Markdown Handling', () => {
    it('should parse markdown with table without crashing', () => {
      expect(() => {
        parseMarkdownToMindmap(MARKDOWN_WITH_TABLE);
      }).not.toThrow();
    });

    it('should extract nodes from markdown with table', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_TABLE);
      
      // Should have multiple nodes
      expect(result.nodes.length).toBeGreaterThan(0);
      
      // Should have edges connecting nodes
      expect(result.edges.length).toBeGreaterThan(0);
    });

    it('should correctly parse headings in markdown with table', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_TABLE);
      
      // Check for expected headings
      const headingContents = result.nodes.map(n => n.content);
      expect(headingContents.some(c => c.includes('输出量的误区'))).toBe(true);
      expect(headingContents.some(c => c.includes('构建你的独特信号'))).toBe(true);
      expect(headingContents.some(c => c.includes('核心要点'))).toBe(true);
    });

    it('should skip table rows as they are not valid mindmap nodes', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_TABLE);
      
      // Table separator lines should not create nodes
      const nodeContents = result.nodes.map(n => n.content);
      expect(nodeContents.some(c => c === '------')).toBe(false);
      expect(nodeContents.some(c => c === '|------|------|--------|')).toBe(false);
    });
  });

  describe('Source Marker Extraction', () => {
    it('should extract TIME markers correctly', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_MARKERS);
      
      const nodesWithTimeRefs = result.nodes.filter(
        n => n.sourceRefs && n.sourceRefs.some(ref => ref.sourceType === 'video')
      );
      
      expect(nodesWithTimeRefs.length).toBeGreaterThan(0);
    });

    it('should extract PAGE markers correctly', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_MARKERS);
      
      const nodesWithPageRefs = result.nodes.filter(
        n => n.sourceRefs && n.sourceRefs.some(ref => ref.sourceType === 'document')
      );
      
      expect(nodesWithPageRefs.length).toBeGreaterThan(0);
    });

    it('should remove markers from node content', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_MARKERS);
      
      result.nodes.forEach(node => {
        expect(node.content).not.toContain('[TIME:');
        expect(node.content).not.toContain('[PAGE:');
        expect(node.content).not.toContain('[Page');
      });
    });

    it('should extract markers from table markdown', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_TABLE);
      
      const nodesWithRefs = result.nodes.filter(
        n => n.sourceRefs && n.sourceRefs.length > 0
      );
      
      // Should have nodes with source references
      expect(nodesWithRefs.length).toBeGreaterThan(0);
    });
  });

  describe('Heading Hierarchy', () => {
    it('should establish correct parent-child relationships', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_ROOT);
      
      // Find ## headings
      const level2Headings = result.nodes.filter(n => n.depth === 1);
      
      // All level 2 headings should have the root as parent
      const rootNode = result.nodes.find(n => n.depth === 0);
      level2Headings.forEach(heading => {
        expect(heading.parentId).toBe(rootNode?.id);
      });
    });

    it('should attach bullet points to nearest heading', () => {
      const result = parseMarkdownToMindmap(MARKDOWN_WITH_ROOT);
      
      // Find bullet points (depth > 1)
      const bulletPoints = result.nodes.filter(n => n.depth > 1);
      
      // Each bullet should have a parent
      bulletPoints.forEach(bullet => {
        expect(bullet.parentId).toBeDefined();
        
        // Parent should exist in nodes
        const parent = result.nodes.find(n => n.id === bullet.parentId);
        expect(parent).toBeDefined();
      });
    });

    it('should handle mixed heading levels correctly', () => {
      const mixedMarkdown = `# Root
## Level 2
### Level 3
- Bullet under level 3
## Another Level 2
- Bullet under level 2`;

      const result = parseMarkdownToMindmap(mixedMarkdown);
      
      // Should have correct depth assignments
      const depths = result.nodes.map(n => n.depth);
      expect(depths).toContain(0); // Root
      expect(depths).toContain(1); // ## headings
      expect(depths).toContain(2); // ### heading
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty markdown', () => {
      const result = parseMarkdownToMindmap('');
      
      expect(result.nodes.length).toBe(0);
      expect(result.edges.length).toBe(0);
      expect(result.rootId).toBeNull();
    });

    it('should handle markdown with only whitespace', () => {
      const result = parseMarkdownToMindmap('   \n\n   \n');
      
      expect(result.nodes.length).toBe(0);
    });

    it('should handle markdown with only bullet points (no headings)', () => {
      const bulletOnly = `- First item
- Second item
  - Nested item`;

      const result = parseMarkdownToMindmap(bulletOnly);
      
      // Should still create nodes
      expect(result.nodes.length).toBeGreaterThan(0);
    });

    it('should handle very long content', () => {
      const longContent = `# Root
- ${'Very long content '.repeat(100)}`;

      const result = parseMarkdownToMindmap(longContent);
      
      // Label should be truncated
      const bulletNode = result.nodes.find(n => n.depth > 0);
      expect(bulletNode?.label.length).toBeLessThanOrEqual(50);
      
      // But content should be preserved
      expect(bulletNode?.content.length).toBeGreaterThan(50);
    });
  });
});
