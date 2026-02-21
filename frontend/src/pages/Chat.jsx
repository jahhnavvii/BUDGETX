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

                // Show analytics summary in chat
                const analytics = data.analytics;
                const summary = [`File "${data.filename}" analyzed successfully.`, ''];

                if (analytics.is_financial_data) {
                    summary.push(
                        `Total Income: $${analytics.total_income.toLocaleString()}`,
                        `Total Expenses: $${analytics.total_expenses.toLocaleString()}`,
                        `Net Surplus: $${analytics.net_surplus.toLocaleString()}`,
                        `Savings Rate: ${analytics.savings_rate}%`
                    );

                    if (analytics.overspending_flags && analytics.overspending_flags.length > 0) {
                        summary.push('', 'Overspending detected:');
                        analytics.overspending_flags.forEach((f) => {
                            summary.push(`- ${f.category}: ${f.percentage}% ($${f.amount.toLocaleString()})`);
                        });
                    }
                } else {
                    summary.push(
                        `Columns detected: ${analytics.columns.join(', ')}`,
                        `Total Rows: ${analytics.total_rows}`
                    );
                    if (analytics.numeric_summary) {
                        summary.push('', 'Numeric data detected. You can ask me to analyze these metrics.');
                    }
                }

                summary.push('', 'Transactions/Rows: ' + analytics.total_rows);
                summary.push('', 'You can now ask me questions about this data.');

                setMessages((prev) => [
                    ...prev,
                    { role: 'user', content: `Uploaded file: ${data.filename}` },
                    { role: 'assistant', content: summary.join('\n') },
                ]);
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
                    <h4 className="sidebar-label">Views</h4>
                    <button
                        className={`view-toggle-btn ${viewMode === 'chat' ? 'active' : ''}`}
                        onClick={() => setViewMode('chat')}
                    >
                        <MessageSquare size={16} />
                        <span>Chat</span>
                    </button>
                    <button
                        className={`view-toggle-btn ${viewMode === 'dashboard' ? 'active' : ''}`}
                        onClick={() => setViewMode('dashboard')}
                        disabled={!activeFileId}
                    >
                        <LayoutDashboard size={16} />
                        <span>Dashboard</span>
                    </button>
                </div>

                {activeFileId && (
                    <div className="sidebar-section">
                        <div className="active-file-badge">
                            <BarChart3 size={14} />
                            <span>Analytics active</span>
                        </div>
                    </div>
                )}
            </aside>

            <div className="chat-main">
                {viewMode === 'chat' ? (
                    <>
                        <div className="chat-messages">
                            {messages.length === 0 && (
                                <div className="chat-welcome">
                                    <div className="welcome-icon">
                                        <BarChart3 size={40} />
                                    </div>
                                    <h2 className="welcome-title">Welcome to BudgetX</h2>
                                    <p className="welcome-text">
                                        Upload a CSV file with your financial data to get started,
                                        or ask me anything about budgeting and financial optimization.
                                    </p>
                                    <div className="welcome-hints">
                                        <div className="hint-item">
                                            <AlertCircle size={14} />
                                            Flexible CSV support: Use any CSV file. For financial optimization, include: date, category, amount, type (income/expense).
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
                                        <div className="message-content">{msg.content}</div>
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
                                    disabled={!input.trim() || loading}
                                >
                                    <Send size={18} />
                                </button>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="dashboard-view">
                        <DashboardContainer activeFileId={activeFileId} files={files} />
                    </div>
                )}
            </div>
        </div>
    );
}

const DashboardContainer = ({ activeFileId, files }) => {
    const activeFile = files.find(f => f.id === activeFileId);
    if (!activeFile || !activeFile.analytics_json) {
        return <div className="dashboard-empty">Select a file with analytics to view dashboard</div>;
    }

    const analytics = JSON.parse(activeFile.analytics_json);
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
        <div className="dashboard-content">
            <div className="dashboard-header">
                <h2 className="dashboard-title">Analysis for {activeFile.filename}</h2>
                <div className="dashboard-timestamp">Uploaded on {new Date(activeFile.upload_date).toLocaleDateString()}</div>
            </div>

            <div className="metric-grid">
                <div className="metric-card">
                    <div className="metric-icon income"><DollarSign size={20} /></div>
                    <div className="metric-info">
                        <div className="metric-label">Total Rows</div>
                        <div className="metric-value">{analytics.total_rows}</div>
                    </div>
                </div>
                {isFinancial && (
                    <>
                        <div className="metric-card">
                            <div className="metric-icon surplus"><TrendingUp size={20} /></div>
                            <div className="metric-info">
                                <div className="metric-label">Savings Rate</div>
                                <div className="metric-value">{analytics.savings_rate}%</div>
                            </div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-icon expense"><Wallet size={20} /></div>
                            <div className="metric-info">
                                <div className="metric-label">Net Surplus</div>
                                <div className="metric-value">${analytics.net_surplus.toLocaleString()}</div>
                            </div>
                        </div>
                    </>
                )}
            </div>

            <div className="chart-grid">
                {isFinancial ? (
                    <>
                        <div className="chart-card">
                            <h3 className="chart-title">Income vs Expenses</h3>
                            <div className="chart-container">
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={barData}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip />
                                        <Bar dataKey="amount" fill="#9FA8DA" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                        <div className="chart-card">
                            <h3 className="chart-title">Expense Distribution</h3>
                            <div className="chart-container">
                                <ResponsiveContainer width="100%" height={300}>
                                    <PieChart>
                                        <Pie
                                            data={pieData}
                                            innerRadius={60}
                                            outerRadius={100}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {pieData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip />
                                        <Legend verticalAlign="bottom" height={36} />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="chart-card wide">
                        <h3 className="chart-title">General Data Summary</h3>
                        <div className="generic-summary">
                            <p><strong>Columns:</strong> {analytics.columns.join(', ')}</p>
                            <p><strong>Data Types:</strong></p>
                            <ul className="dtype-list">
                                {Object.entries(analytics.data_types).map(([col, type]) => (
                                    <li key={col}>{col}: <span className="type-tag">{type}</span></li>
                                ))}
                            </ul>
                        </div>
                    </div>
                )}
            </div>

            {isFinancial && analytics.overspending_flags && analytics.overspending_flags.length > 0 && (
                <div className="insights-section">
                    <h3 className="section-title">Critical Insights</h3>
                    <div className="insight-grid">
                        {analytics.overspending_flags.map((flag, i) => (
                            <div key={i} className="insight-card warning">
                                <AlertCircle size={20} className="insight-icon" />
                                <div className="insight-text">
                                    <strong>High Spending in {flag.category}</strong>
                                    <p>This category accounts for {flag.percentage}% of your total expenses (${flag.amount.toLocaleString()}).</p>
                                </div>
                                <ChevronRight size={16} className="insight-arrow" />
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Chat;
