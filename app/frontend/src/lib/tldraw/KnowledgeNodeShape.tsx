/**
 * Custom Knowledge Node shape for tldraw
 * Represents a node in the knowledge graph canvas
 */

import {
  BaseBoxShapeUtil,
  DefaultColorStyle,
  HTMLContainer,
  RecordProps,
  Rectangle2d,
  T,
  TLBaseShape,
  TLDefaultColorStyle,
} from 'tldraw'

// Define the shape type
export type KnowledgeNodeShape = TLBaseShape<
  'knowledge-node',
  {
    w: number
    h: number
    title: string
    content: string
    color: TLDefaultColorStyle
    tags: string[]
    sourceId?: string
    sourcePage?: number
  }
>

// Validation schema
export const knowledgeNodeShapeProps: RecordProps<KnowledgeNodeShape> = {
  w: T.number,
  h: T.number,
  title: T.string,
  content: T.string,
  color: DefaultColorStyle,
  tags: T.arrayOf(T.string),
  sourceId: T.string.optional(),
  sourcePage: T.number.optional(),
}

export class KnowledgeNodeUtil extends BaseBoxShapeUtil<KnowledgeNodeShape> {
  static override type = 'knowledge-node' as const
  static override props = knowledgeNodeShapeProps

  override isAspectRatioLocked = (_shape: KnowledgeNodeShape) => false
  override canResize = (_shape: KnowledgeNodeShape) => true
  override canBind = (_shape: KnowledgeNodeShape) => true

  getDefaultProps(): KnowledgeNodeShape['props'] {
    return {
      w: 280,
      h: 200,
      title: 'New Node',
      content: '',
      color: 'blue',
      tags: [],
    }
  }

  override getGeometry(shape: KnowledgeNodeShape): Rectangle2d {
    return new Rectangle2d({
      width: shape.props.w,
      height: shape.props.h,
      isFilled: true,
    })
  }

  component(shape: KnowledgeNodeShape) {
    const bounds = this.getGeometry(shape).bounds
    const { title, content, tags, sourceId, sourcePage } = shape.props

    return (
      <HTMLContainer
        id={shape.id}
        style={{
          width: bounds.width,
          height: bounds.height,
          display: 'flex',
          flexDirection: 'column',
          background: 'white',
          border: '2px solid #E5E7EB',
          borderRadius: '12px',
          padding: '16px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
          overflow: 'hidden',
          pointerEvents: 'all',
        }}
      >
        {/* Header */}
        <div
          style={{
            fontSize: '16px',
            fontWeight: '600',
            color: '#1F2937',
            marginBottom: '8px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
          }}
        >
          {title}
        </div>

        {/* Content */}
        {content && (
          <div
            style={{
              fontSize: '14px',
              color: '#6B7280',
              marginBottom: '12px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 4,
              WebkitBoxOrient: 'vertical',
              flex: 1,
            }}
          >
            {content}
          </div>
        )}

        {/* Footer */}
        <div style={{ marginTop: 'auto' }}>
          {/* Tags */}
          {tags.length > 0 && (
            <div
              style={{
                display: 'flex',
                gap: '6px',
                flexWrap: 'wrap',
                marginBottom: '8px',
              }}
            >
              {tags.slice(0, 3).map((tag, i) => (
                <span
                  key={i}
                  style={{
                    fontSize: '11px',
                    padding: '2px 8px',
                    background: '#EFF6FF',
                    color: '#3B82F6',
                    borderRadius: '4px',
                    fontWeight: '500',
                  }}
                >
                  {tag}
                </span>
              ))}
              {tags.length > 3 && (
                <span
                  style={{
                    fontSize: '11px',
                    padding: '2px 8px',
                    background: '#F3F4F6',
                    color: '#6B7280',
                    borderRadius: '4px',
                  }}
                >
                  +{tags.length - 3}
                </span>
              )}
            </div>
          )}

          {/* Source info */}
          {sourceId && (
            <div
              style={{
                fontSize: '11px',
                color: '#9CA3AF',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <span>📄</span>
              <span>
                {sourceId.substring(0, 8)}
                {sourcePage ? ` • p.${sourcePage}` : ''}
              </span>
            </div>
          )}
        </div>
      </HTMLContainer>
    )
  }

  indicator(shape: KnowledgeNodeShape) {
    const bounds = this.getGeometry(shape).bounds
    return (
      <rect
        width={bounds.width}
        height={bounds.height}
        rx={12}
        ry={12}
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
      />
    )
  }
}






























