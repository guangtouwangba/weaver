'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { commentsApi, CommentResponse } from '@/lib/api';
import { Send, MessageCircle, Trash2, ChevronDown, ChevronRight, User } from 'lucide-react';

interface CommentsPanelProps {
    documentId: string;
}

export default function CommentsPanel({ documentId }: CommentsPanelProps) {
    const [comments, setComments] = useState<CommentResponse[]>([]);
    const [totalCount, setTotalCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [newComment, setNewComment] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [expandedComments, setExpandedComments] = useState<Set<string>>(new Set());
    const [replies, setReplies] = useState<Record<string, CommentResponse[]>>({});
    const [replyingTo, setReplyingTo] = useState<string | null>(null);
    const [replyText, setReplyText] = useState('');

    // Load comments
    const loadComments = useCallback(async () => {
        if (!documentId) return;

        setLoading(true);
        try {
            const response = await commentsApi.list(documentId);
            setComments(response.comments);
            setTotalCount(response.total);
        } catch (error) {
            console.error('Failed to load comments:', error);
        } finally {
            setLoading(false);
        }
    }, [documentId]);

    useEffect(() => {
        loadComments();
    }, [loadComments]);

    // Submit new comment
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newComment.trim() || submitting) return;

        setSubmitting(true);
        try {
            const created = await commentsApi.create(documentId, {
                content: newComment.trim(),
                author_name: 'You', // TODO: Get from auth
            });
            setComments(prev => [created, ...prev]);
            setTotalCount(prev => prev + 1);
            setNewComment('');
        } catch (error) {
            console.error('Failed to create comment:', error);
        } finally {
            setSubmitting(false);
        }
    };

    // Submit reply
    const handleReplySubmit = async (parentId: string) => {
        if (!replyText.trim() || submitting) return;

        setSubmitting(true);
        try {
            const created = await commentsApi.create(documentId, {
                content: replyText.trim(),
                parent_id: parentId,
                author_name: 'You',
            });
            setReplies(prev => ({
                ...prev,
                [parentId]: [...(prev[parentId] || []), created],
            }));
            // Update reply count in parent
            setComments(prev => prev.map(c =>
                c.id === parentId ? { ...c, reply_count: c.reply_count + 1 } : c
            ));
            setReplyText('');
            setReplyingTo(null);
        } catch (error) {
            console.error('Failed to create reply:', error);
        } finally {
            setSubmitting(false);
        }
    };

    // Load replies for a comment
    const loadReplies = async (commentId: string) => {
        try {
            const replyList = await commentsApi.listReplies(documentId, commentId);
            setReplies(prev => ({ ...prev, [commentId]: replyList }));
        } catch (error) {
            console.error('Failed to load replies:', error);
        }
    };

    // Toggle expand/collapse replies
    const toggleExpanded = (commentId: string, replyCount: number) => {
        if (expandedComments.has(commentId)) {
            setExpandedComments(prev => {
                const next = new Set(prev);
                next.delete(commentId);
                return next;
            });
        } else {
            setExpandedComments(prev => new Set(prev).add(commentId));
            if (!replies[commentId] && replyCount > 0) {
                loadReplies(commentId);
            }
        }
    };

    // Delete comment
    const handleDelete = async (commentId: string, parentId?: string) => {
        try {
            await commentsApi.delete(documentId, commentId);
            if (parentId) {
                // Remove from replies
                setReplies(prev => ({
                    ...prev,
                    [parentId]: (prev[parentId] || []).filter(r => r.id !== commentId),
                }));
                // Update parent reply count
                setComments(prev => prev.map(c =>
                    c.id === parentId ? { ...c, reply_count: Math.max(0, c.reply_count - 1) } : c
                ));
            } else {
                // Remove from top-level comments
                setComments(prev => prev.filter(c => c.id !== commentId));
                setTotalCount(prev => prev - 1);
            }
        } catch (error) {
            console.error('Failed to delete comment:', error);
        }
    };

    const formatTime = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        const diffDays = Math.floor(diffHours / 24);
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    const CommentItem = ({ comment, isReply = false, parentId }: {
        comment: CommentResponse;
        isReply?: boolean;
        parentId?: string;
    }) => {
        const isExpanded = expandedComments.has(comment.id);
        const commentReplies = replies[comment.id] || [];

        return (
            <div className={`${isReply ? 'ml-6 border-l-2 border-stone-100 pl-4' : ''}`}>
                <div className="group py-3">
                    {/* Header */}
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center">
                            <User size={12} className="text-white" />
                        </div>
                        <span className="text-sm font-medium text-stone-700">{comment.author_name}</span>
                        <span className="text-xs text-stone-400">{formatTime(comment.created_at)}</span>
                        {comment.page_number && (
                            <span className="text-xs bg-stone-100 text-stone-500 px-1.5 py-0.5 rounded">
                                Page {comment.page_number}
                            </span>
                        )}
                        {/* Delete button */}
                        <button
                            onClick={() => handleDelete(comment.id, parentId)}
                            className="ml-auto opacity-0 group-hover:opacity-100 p-1 text-stone-400 hover:text-red-500 transition-opacity"
                        >
                            <Trash2 size={14} />
                        </button>
                    </div>

                    {/* Content */}
                    <p className="text-sm text-stone-600 leading-relaxed">{comment.content}</p>

                    {/* Actions */}
                    <div className="flex items-center gap-3 mt-2">
                        {!isReply && (
                            <button
                                onClick={() => setReplyingTo(replyingTo === comment.id ? null : comment.id)}
                                className="text-xs text-stone-400 hover:text-teal-500 transition-colors"
                            >
                                Reply
                            </button>
                        )}
                        {!isReply && comment.reply_count > 0 && (
                            <button
                                onClick={() => toggleExpanded(comment.id, comment.reply_count)}
                                className="text-xs text-stone-400 hover:text-teal-500 transition-colors flex items-center gap-1"
                            >
                                {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                {comment.reply_count} {comment.reply_count === 1 ? 'reply' : 'replies'}
                            </button>
                        )}
                    </div>

                    {/* Reply input */}
                    {replyingTo === comment.id && (
                        <div className="mt-3 flex gap-2">
                            <input
                                type="text"
                                value={replyText}
                                onChange={(e) => setReplyText(e.target.value)}
                                placeholder="Write a reply..."
                                className="flex-1 text-sm px-3 py-2 border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                                onKeyDown={(e) => e.key === 'Enter' && handleReplySubmit(comment.id)}
                            />
                            <button
                                onClick={() => handleReplySubmit(comment.id)}
                                disabled={!replyText.trim() || submitting}
                                className="px-3 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Send size={14} />
                            </button>
                        </div>
                    )}
                </div>

                {/* Replies */}
                {isExpanded && commentReplies.map(reply => (
                    <CommentItem key={reply.id} comment={reply} isReply parentId={comment.id} />
                ))}
            </div>
        );
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header with count */}
            <div className="flex items-center gap-2 mb-4">
                <MessageCircle size={16} className="text-stone-400" />
                <span className="text-sm font-medium text-stone-600">
                    {totalCount} {totalCount === 1 ? 'comment' : 'comments'}
                </span>
            </div>

            {/* New comment input */}
            <form onSubmit={handleSubmit} className="mb-4">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Add a comment..."
                        className="flex-1 text-sm px-3 py-2 border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                    />
                    <button
                        type="submit"
                        disabled={!newComment.trim() || submitting}
                        className="px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send size={16} />
                    </button>
                </div>
            </form>

            {/* Comments list */}
            <div className="flex-1 overflow-y-auto min-h-0 divide-y divide-stone-100">
                {loading ? (
                    <div className="py-8 text-center text-stone-400 text-sm">Loading comments...</div>
                ) : comments.length === 0 ? (
                    <div className="py-8 text-center text-stone-400 text-sm">
                        No comments yet.<br />Be the first to comment!
                    </div>
                ) : (
                    comments.map(comment => (
                        <CommentItem key={comment.id} comment={comment} />
                    ))
                )}
            </div>
        </div>
    );
}
