import { useState, useRef, useEffect } from 'react';
import { Send, Upload, Trash2, FileText, BarChart3, AlertCircle, LayoutDashboard, MessageSquare, ChevronRight, TrendingUp, DollarSign, Wallet } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell } from 'recharts';
import './Chat.css';

const API = 'http://127.0.0.1:8000/api';

function Chat({ token, username }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [files, setFiles] = useState([]);
    const [activeFileId, setActiveFileId] = useState(null);
    const [uploadingFile, setUploadingFile] = useState(false);
    const [viewMode, setViewMode] = useState('chat'); // 'chat' or 'dashboard'
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

    const MessageContent = ({ content }) => {
        const dashboardRegex = /\[DASHBOARD_DATA\]([\s\S]*?)\[\/DASHBOARD_DATA\]/;
        const match = content.match(dashboardRegex);

        if (match) {
            const textContent = content.replace(dashboardRegex, '').trim();
            let analytics = null;
            try {
                analytics = JSON.parse(match[1]);
            } catch (e) {
                console.error("Failed to parse inline dashboard data", e);
            }

            return (
                <div className="message-content-wrapper">
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

                    {messages.map((msg, i) => (
                        <div key={i} className={`message ${msg.role}`}>
                            <div className="message-avatar">
                                {msg.role === 'user' ? username[0].toUpperCase() : 'B'}
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
                    ))}

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

const InlineDashboard = ({ analytics }) => {
    const isFinancial = analytics.is_financial_data;
    const COLORS = ['#9FA8DA', '#81C784', '#FFB74D', '#4DB6AC', '#FF8A65', '#BA68C8'];

    const barData = isFinancial ? [
        { name: 'Income', amount: analytics.total_income },
        { name: 'Expenses', amount: analytics.total_expenses },
        { name: 'Surplus', amount: analytics.net_surplus }
    ] : [];

    const pieData = (isFinancial && analytics.expense_by_category) ?
        Object.entries(analytics.expense_by_category).map(([name, value]) => ({ name, value })) : [];

    return (
        <div className="inline-dashboard-content">
            <div className="metric-grid-inline">
                <div className="metric-pill">
                    <span className="pill-label">Rows:</span>
                    <span className="pill-value">{analytics.total_rows}</span>
                </div>
                {isFinancial && (
                    <>
                        <div className="metric-pill surplus-pill">
                            <TrendingUp size={12} />
                            <span>{analytics.savings_rate}% Savings</span>
                        </div>
                        <div className="metric-pill wallet-pill">
                            <Wallet size={12} />
                            <span>${analytics.net_surplus.toLocaleString()}</span>
                        </div>
                    </>
                )}
            </div>

            <div className="chart-grid-inline">
                {isFinancial || (analytics.expense_by_category && Object.keys(analytics.expense_by_category).length > 0) ? (
                    <>
                        <div className="chart-item">
                            <h4 className="chart-label-inline">{analytics.generic_chart_label || "Income vs Expenses"}</h4>
                            <div className="chart-wrapper-inline">
                                <ResponsiveContainer width="100%" height={200}>
                                    {isFinancial && analytics.total_income ? (
                                        <BarChart data={barData}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                                            <XAxis dataKey="name" fontSize={10} tick={{ fill: '#666' }} />
                                            <YAxis fontSize={10} tick={{ fill: '#666' }} />
                                            <Tooltip />
                                            <Bar dataKey="amount" fill="#9FA8DA" radius={[4, 4, 0, 0]} />
                                        </BarChart>
                                    ) : (
                                        <BarChart data={pieData.slice(0, 8)}>
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
                            <div className="chart-wrapper-inline">
                                <ResponsiveContainer width="100%" height={200}>
                                    <PieChart>
                                        <Pie
                                            data={pieData.slice(0, 10)}
                                            innerRadius={40}
                                            outerRadius={70}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {pieData.slice(0, 10).map((entry, index) => (
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
                        <p className="generic-title">Generic Data Detected</p>
                        <p className="generic-cols">Columns: {analytics.columns.join(', ')}</p>
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

export default Chat;

