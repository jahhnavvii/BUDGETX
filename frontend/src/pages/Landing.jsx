import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Droplets, Users, Briefcase, User, ArrowRight } from 'lucide-react';
import './Landing.css';

function Landing() {
    const navigate = useNavigate();

    useEffect(() => {
        const handleMouseMove = (e) => {
            const cards = document.getElementsByClassName('feature-card');
            for (const card of cards) {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                card.style.setProperty('--mouse-x', `${x}px`);
                card.style.setProperty('--mouse-y', `${y}px`);
            }
        };

        window.addEventListener('mousemove', handleMouseMove);
        return () => window.removeEventListener('mousemove', handleMouseMove);
    }, []);

    return (
        <main className="landing">
            <div className="banner-gradient global-mesh"></div>
            {/* Banner Section */}
            <section className="banner-section">
                <div className="banner-wrapper">
                    <div className="banner-image">
                        <div className="floating-blob blob-1"></div>
                        <div className="floating-blob blob-2"></div>
                        <div className="banner-content">
                            <h1 className="banner-title">Smart Financial Decisions,<br />Powered by AI</h1>
                            <p className="banner-subtitle">
                                Analyze your spending, optimize your budget, and grow your wealth with intelligent insights.
                            </p>
                            <button className="btn-try-now" onClick={() => navigate('/login')}>
                                Try Now
                                <ArrowRight size={18} />
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            {/* What is BudgetX */}
            <section className="about-section" id="about">
                <div className="section-container">
                    <h2 className="section-title">What is BudgetX?</h2>
                    <p className="section-description">
                        BudgetX is an AI-driven cost optimization platform. It analyzes individual spending
                        habits to generate tailored recommendations, thereby enhancing the user's financial literacy.
                    </p>
                </div>
            </section>

            {/* Feature Cards */}
            <section className="features-section" id="features">
                <div className="section-container">
                    <div className="features-grid">
                        <div className="feature-card card-1">
                            <div className="feature-icon">
                                <TrendingUp size={28} />
                            </div>
                            <h3 className="feature-title">Capital that Grows</h3>
                            <p className="feature-text">
                                Intelligent investment suggestions based on your surplus analysis. Make your money
                                work harder with data-driven growth strategies.
                            </p>
                        </div>

                        <div className="feature-card card-2">
                            <div className="feature-icon">
                                <Droplets size={28} />
                            </div>
                            <h3 className="feature-title">Always Liquid, Always Stable</h3>
                            <p className="feature-text">
                                Maintain optimal liquidity ratios. Get alerts when your emergency fund dips below
                                recommended levels and keep finances stable.
                            </p>
                        </div>

                        <div className="feature-card card-3">
                            <div className="feature-icon">
                                <Users size={28} />
                            </div>
                            <h3 className="feature-title">User Friendly</h3>
                            <p className="feature-text">
                                Simple CSV upload, clear visualizations, and plain-language AI explanations.
                                No financial expertise required to get started.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Use Cases */}
            <section className="usecase-section">
                <div className="section-container">
                    <h2 className="section-title">Use Cases</h2>
                    <div className="usecase-grid">
                        <div className="usecase-card">
                            <div className="usecase-icon">
                                <Briefcase size={32} />
                            </div>
                            <h3 className="usecase-name">Business</h3>
                            <p className="usecase-text">
                                Track operational expenses, identify cost inefficiencies, and optimize
                                departmental budgets with AI-powered analysis.
                            </p>
                        </div>

                        <div className="usecase-card">
                            <div className="usecase-icon">
                                <User size={32} />
                            </div>
                            <h3 className="usecase-name">Personal</h3>
                            <p className="usecase-text">
                                Understand your spending patterns, reduce unnecessary expenses, and build
                                a healthier financial future with personalized insights.
                            </p>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}

export default Landing;
