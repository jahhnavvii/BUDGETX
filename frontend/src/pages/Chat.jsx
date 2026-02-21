import { useState, useRef, useEffect } from 'react';
import { Send, Upload, Trash2, FileText, BarChart3, AlertCircle, TrendingUp, Wallet, ShieldAlert, Scissors, Target, LineChart, PieChart as PieChartIcon, MessageSquare } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell } from 'recharts';
import './Chat.css';


const API = 'http://127.0.0.1:8000/api';

// ---------------- Helper Components ----------------

const MessageContent = ({ content }) => {
    // Improved regex to handle optional markdown code block wrappers
    const dashboardRegex = /\[DASHBOARD_DATA\]([\s\S]*?)\[\/DASHBOARD_DATA\]/;
    const match = content.match(dashboardRegex);

    if (match) {
        let textContent = content.replace(dashboardRegex, '').trim();
        // Clean up potential empty code blocks left behind
        textContent = textContent.replace(/```json\s*```/g, '').trim();

        let analytics = null;
        try {
            // Clean match of any markdown code block if present
            const jsonStr = match[1].replace(/```json|```/g, '').trim();
            analytics = JSON.parse(jsonStr);
        } catch (e) {
            console.error("Failed to parse inline dashboard data", e);
        }

        return (
            <div className="message-content-wrapper" style={{ width: '100%' }}>
                {textContent && <div className="text-content">{textContent}</div>}
                {analytics && (
                    <div className="inline-dashboard">
                        <InlineDashboard analytics={analytics} />
                    </div>
                )}
            </div>
        );
    }

    return <div className="text-content">{content}</div>;
};

const InlineDashboard = ({ analytics }) => {
    const isFinancial = analytics.is_financial_data;
    const COLORS = ['#9FA8DA', '#81C784', '#FFB74D', '#4DB6AC', '#FF8A65', '#BA68C8'];

    const barData = isFinancial ? [
        { name: 'Income', amount: analytics.total_income || 0 },
        { name: 'Expenses', amount: analytics.total_expenses || 0 },
        { name: 'Surplus', amount: analytics.net_surplus || 0 }
    ] : [];

    const pieItems = (analytics.expense_by_category && typeof analytics.expense_by_category === 'object') ?
        Object.entries(analytics.expense_by_category).map(([name, value]) => ({ name, value })) : [];

    const hasNoData = pieItems.length === 0 && barData.every(d => d.amount === 0);

    if (hasNoData) {
        return (
            <div className="inline-dashboard-empty">
                <p>No detailed chart data available for this view.</p>
            </div>
        );
    }

    return (
        <div className="inline-dashboard-content" style={{ width: '100%' }}>
            <div className="metric-grid-inline">
                <div className="metric-pill">
                    <span className="pill-label">Rows:</span>
                    <span className="pill-value">{analytics.total_rows}</span>
                </div>
                {isFinancial && analytics.savings_rate !== undefined && (
                    <div className="metric-pill surplus-pill">
                        <TrendingUp size={12} />
                        <span>{analytics.savings_rate}% Savings</span>
                    </div>
                )}
                {isFinancial && analytics.net_surplus !== undefined && (
                    <div className="metric-pill wallet-pill">
                        <Wallet size={12} />
                        <span>${analytics.net_surplus?.toLocaleString()}</span>
                    </div>
                )}
            </div>

            <div className="chart-grid-inline">
                {(isFinancial && (analytics.total_income > 0 || analytics.total_expenses > 0)) || (pieItems.length > 0) ? (
                    <>
                        <div className="chart-item">
                            <h4 className="chart-label-inline">{analytics.generic_chart_label || "Income vs Expenses"}</h4>
                            <div className="chart-wrapper-inline" style={{ width: '100%', height: '200px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    {isFinancial && (analytics.total_income > 0 || analytics.total_expenses > 0) ? (
                                        <BarChart data={barData}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                                            <XAxis dataKey="name" fontSize={10} tick={{ fill: '#666' }} />
                                            <YAxis fontSize={10} tick={{ fill: '#666' }} />
                                            <Tooltip />
                                            <Bar dataKey="amount" fill="#9FA8DA" radius={[4, 4, 0, 0]} />
                                        </BarChart>
                                    ) : (
                                        <BarChart data={pieItems.slice(0, 8)}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                                            <XAxis dataKey="name" fontSize={10} tick={{ fill: '#666' }} />
                                            <YAxis fontSize={10} tick={{ fill: '#666' }} />
                                            <Tooltip />
                                            <Bar dataKey="value" fill="#9FA8DA" radius={[4, 4, 0, 0]} />
                                        </BarChart>
                                    )}
                                </ResponsiveContainer>
                            </div>
                        </div>
                        <div className="chart-item">
                            <h4 className="chart-label-inline">Distribution</h4>
                            <div className="chart-wrapper-inline" style={{ width: '100%', height: '200px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={pieItems.slice(0, 10)}
                                            innerRadius={40}
                                            outerRadius={70}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {pieItems.slice(0, 10).map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="generic-data-inline">
                        <p className="generic-title">Generic Data Summary</p>
                        <p className="generic-cols">Columns: {analytics.columns?.join(', ')}</p>
                    </div>
                )}
            </div>

            {isFinancial && analytics.overspending_flags && analytics.overspending_flags.length > 0 && (
                <div className="inline-alerts">
                    {analytics.overspending_flags.map((flag, i) => (
                        <div key={i} className="mini-alert">
                            <AlertCircle size={12} />
                            <span><strong>{flag.category}</strong>: {flag.percentage}% of spending</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const REPORT_TYPES = [
    {
        key: 'risk_assessment',
        icon: ShieldAlert,
        title: 'Risk Assessment',
        subtitle: 'Financial health score, liquidity & volatility analysis',
        color: '#ef4444',
        bg: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%)'
    },
    {
        key: 'cost_optimization',
        icon: Scissors,
        title: 'Cost Optimization',
        subtitle: 'Spending inefficiencies, benchmarks & savings opportunities',
        color: '#22c55e',
        bg: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(34, 197, 94, 0.05) 100%)'
    },
    {
        key: 'strategic_recommendations',
        icon: Target,
        title: 'Strategic Recommendations',
        subtitle: 'Short, medium & long-term action roadmap',
        color: '#f59e0b',
        bg: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%)'
    },
    {
        key: 'performance_analytics',
        icon: LineChart,
        title: 'Performance Analytics',
        subtitle: 'KPIs, trends, variance & profitability analysis',
        color: '#3b82f6',
        bg: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%)'
    },
    {
        key: 'investment_portfolio',
        icon: PieChartIcon,
        title: 'Investment & Portfolio',
        subtitle: 'Asset allocation, risk-return profile & rebalancing',
        color: '#8b5cf6',
        bg: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%)'
    },
];

const ReportOptions = ({ fileId, onRequest, loadingType }) => {
    return (
        <div className="report-options-wrapper">
            <div className="report-options-header">
                <span className="report-options-label">✨ Deep Analysis Reports</span>
                <span className="report-options-hint">Click any report to generate a detailed AI analysis</span>
            </div>
            <div className="report-cards-grid">
                {REPORT_TYPES.map(({ key, icon: Icon, title, subtitle, color, bg }) => {
                    const isLoading = loadingType === key;
                    const isOtherLoading = loadingType && loadingType !== key;
                    return (
                        <button
                            key={key}
                            className={`report-card ${isLoading ? 'loading' : ''} ${isOtherLoading ? 'dimmed' : ''}`}
                            style={{ '--card-color': color, '--card-bg': bg }}
                            onClick={() => onRequest(key, fileId)}
                            disabled={!!loadingType}
                        >
                            <div className="report-card-icon" style={{ color }}>
                                {isLoading ? (
                                    <div className="report-spinner" />
                                ) : (
                                    <Icon size={20} />
                                )}
                            </div>
                            <div className="report-card-content">
                                <span className="report-card-title">{title}</span>
                                <span className="report-card-subtitle">{subtitle}</span>
                            </div>
                            {isLoading && <span className="report-generating">Generating...</span>}
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

function Chat({ token, username }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [files, setFiles] = useState([]);
    const [activeFileId, setActiveFileId] = useState(null);
    const [uploadingFile, setUploadingFile] = useState(false);
    const [reportLoading, setReportLoading] = useState(null); // tracks which report is loading
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };

    // Load chat history on mount
    useEffect(() => {
        loadHistory();
        loadFiles();
    }, []);

    // Auto-scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadHistory = async () => {
        try {
            const res = await fetch(`${API}/chat/history`, { headers });
            if (res.ok) {
                const data = await res.json();
                setMessages(data);
            }
        } catch (err) {
            console.error('Failed to load history:', err);
        }
    };

    const loadFiles = async () => {
        try {
            const res = await fetch(`${API}/files`, { headers });
            if (res.ok) {
                const data = await res.json();
                setFiles(data);
            }
        } catch (err) {
            console.error('Failed to load files:', err);
        }
    };

    const sendMessage = async () => {
        if (!input.trim() || loading) return;

        const userMsg = { role: 'user', content: input.trim() };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const body = { message: userMsg.content };
            if (activeFileId) body.file_id = activeFileId;

            const res = await fetch(`${API}/chat`, {
                method: 'POST',
                headers,
                body: JSON.stringify(body),
            });
            const data = await res.json();

            if (res.ok) {
                setMessages((prev) => [...prev, { role: 'assistant', content: data.content }]);
            } else {
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', content: `Error: ${data.detail || 'Something went wrong'}` },
                ]);
            }
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: 'Failed to connect to the server. Please try again.' },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const requestReport = async (reportType, fileId) => {
        if (reportLoading) return;
        setReportLoading(reportType);

        const labels = {
            risk_assessment: '📊 Risk Assessment',
            cost_optimization: '💰 Cost Optimization',
            strategic_recommendations: '🎯 Strategic Recommendations',
            performance_analytics: '📈 Performance Analytics',
            investment_portfolio: '💹 Investment & Portfolio',
        };

        // Add user request message
        setMessages(prev => [...prev, {
            role: 'user',
            content: `Generate ${labels[reportType]} Report`
        }]);

        try {
            const res = await fetch(`${API}/report`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ file_id: fileId, report_type: reportType }),
            });
            const data = await res.json();

            if (res.ok) {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `**${labels[reportType]} Report — ${data.filename}**\n\n${data.content}`
                }]);
            } else {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `Failed to generate report: ${data.detail || 'Unknown error'}`
                }]);
            }
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Failed to connect to the server for report generation.'
            }]);
        } finally {
            setReportLoading(null);
        }
    };

    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploadingFile(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch(`${API}/upload`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData,
            });
            const data = await res.json();

            if (res.ok) {
                setActiveFileId(data.file_id);
                loadFiles();
                // We don't need to manually add messages here anymore because the backend 
                // now adds the upload and auto-insight messages to the DB history.
                // We just reload history to see the new messages from the AI.
                setTimeout(loadHistory, 500);
            } else {
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', content: `Upload failed: ${data.detail || 'Unknown error'}` },
                ]);
            }
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: 'Failed to upload file. Please check your connection.' },
            ]);
        } finally {
            setUploadingFile(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const clearHistory = async () => {
        try {
            await fetch(`${API}/chat/history`, {
                method: 'DELETE',
                headers,
            });
            setMessages([]);
        } catch (err) {
            console.error('Failed to clear history:', err);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="chat-page">
            <aside className="chat-sidebar">
                <div className="sidebar-header">
                    <h3 className="sidebar-title">BudgetX Chat</h3>
                    <button className="sidebar-btn" onClick={clearHistory} title="Clear history">
                        <Trash2 size={16} />
                    </button>
                </div>

                <div className="sidebar-section">
                    <h4 className="sidebar-label">Uploaded Files</h4>
                    {files.length === 0 && (
                        <p className="sidebar-empty">No files uploaded yet</p>
                    )}
                    {files.map((f) => (
                        <button
                            key={f.id}
                            className={`file-item ${activeFileId === f.id ? 'active' : ''}`}
                            onClick={() => setActiveFileId(f.id)}
                        >
                            <FileText size={14} />
                            <span className="file-name">{f.filename}</span>
                        </button>
                    ))}
                </div>

                <div className="sidebar-section">
                    <div className="active-file-badge">
                        <MessageSquare size={14} />
                        <span>All insights in Chat</span>
                    </div>
                </div>

                {activeFileId && (
                    <div className="sidebar-section">
                        <div className="active-file-badge highlight">
                            <BarChart3 size={14} />
                            <span>Dashboard Active</span>
                        </div>
                    </div>
                )}

                <div className="sidebar-footer">
                    <p className="footer-text">BudgetX AI v2.0</p>
                </div>
            </aside>

            <div className="chat-main">
                <div className="chat-messages">
                    {messages.length === 0 && (
                        <div className="chat-welcome">
                            <div className="welcome-icon">
                                <BarChart3 size={40} />
                            </div>
                            <h2 className="welcome-title">Welcome to BudgetX</h2>
                            <p className="welcome-text">
                                Upload a CSV file and I'll automatically generate insights and a dashboard for you right here in the chat.
                            </p>
                            <div className="welcome-hints">
                                <div className="hint-item">
                                    <AlertCircle size={14} />
                                    No need to ask! Once uploaded, I'll start analyzing your file immediately.
                                </div>
                            </div>
                        </div>
                    )}

                    {messages.map((msg, i) => {
                        const hasDashboard = msg.role === 'assistant' && msg.content.includes('[DASHBOARD_DATA]');
                        const isLastDashboard = hasDashboard && !messages.slice(i + 1).some(m => m.content?.includes('[DASHBOARD_DATA]'));
                        return (
                            <div key={i}>
                                <div className={`message ${msg.role}`}>
                                    <div className="message-avatar">
                                        {msg.role === 'user' ? username[0]?.toUpperCase() : 'B'}
                                    </div>
                                    <div className="message-bubble">
                                        <div className="message-sender">
                                            {msg.role === 'user' ? username : 'BudgetX AI'}
                                        </div>
                                        <div className="message-content">
                                            <MessageContent content={msg.content} />
                                        </div>
                                    </div>
                                </div>
                                {isLastDashboard && activeFileId && (
                                    <ReportOptions
                                        fileId={activeFileId}
                                        onRequest={requestReport}
                                        loadingType={reportLoading}
                                    />
                                )}
                            </div>
                        );
                    })}

                    {loading && (
                        <div className="message assistant">
                            <div className="message-avatar">B</div>
                            <div className="message-bubble">
                                <div className="message-sender">BudgetX AI</div>
                                <div className="typing-indicator">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </div>
                    )}

                    {uploadingFile && (
                        <div className="message assistant">
                            <div className="message-avatar">B</div>
                            <div className="message-bubble">
                                <div className="message-sender">BudgetX AI</div>
                                <div className="upload-status">
                                    <div className="spinner"></div>
                                    <span>Processing file & generating insights...</span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                <div className="chat-input-area">
                    <div className="input-bar">
                        <button
                            className="upload-btn"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={uploadingFile}
                            title="Upload CSV file"
                        >
                            <Upload size={18} />
                        </button>
                        <input
                            type="file"
                            ref={fileInputRef}
                            accept=".csv"
                            onChange={handleUpload}
                            hidden
                        />
                        <textarea
                            className="chat-input"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about your finances..."
                            rows={1}
                        />
                        <button
                            className="send-btn"
                            onClick={sendMessage}
                            disabled={!input.trim() || loading || uploadingFile}
                        >
                            <Send size={18} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Chat;

