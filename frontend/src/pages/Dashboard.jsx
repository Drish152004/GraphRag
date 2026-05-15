import { useState, useRef, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { clearAuthSession, getAuthSession } from "../api/auth"
import { sendChatMessage } from "../api/chat"
import "./Dashboard.css"

export default function Dashboard() {

  const navigate = useNavigate()

  const session = getAuthSession()

  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "ai",
      content: `Here are some sample questions:

• What sustainability initiatives are associated with Apple Inc.?

• Explain what is the purpose of daisy in apples supply chain.

• Which organizations are connected to Apple through supplier programs?

• What recycled materials does Apple aim to use in iPhones?

• How does Apple improve supplier employee development?

• Explain Apple Material Recovery Lab.

• Which entities are related to the Supplier Employee Development Fund?

• What programs has Apple introduced for responsible sourcing?`
    },
  ])

  const [inputValue, setInputValue] = useState("")

  const [isTyping, setIsTyping] = useState(false)

  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {

    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    })
  }

  useEffect(() => {

    scrollToBottom()

  }, [messages, isTyping])

  function handleLogout() {

    clearAuthSession()

    navigate("/")
  }

  const handleSendMessage = async (e) => {

    e.preventDefault()

    if (!inputValue.trim()) return

    const userMessage = {

      id: Date.now(),

      role: "user",

      content: inputValue.trim(),
    }

    setMessages((prev) => [

      ...prev,
      userMessage,
    ])

    setInputValue("")

    setIsTyping(true)

    try {

      const data = await sendChatMessage(userMessage.content)

      const aiMessage = {

        id: Date.now() + 1,

        role: "ai",

        content: data.answer,
      }

      setMessages((prev) => [

        ...prev,
        aiMessage,
      ])

    } catch (error) {

      const errorMessage = {

        id: Date.now() + 1,

        role: "ai",

        content:
          error.message || "Error connecting to GraphRAG backend.",
      }

      setMessages((prev) => [

        ...prev,
        errorMessage,
      ])

    } finally {

      setIsTyping(false)
    }
  }

  return (

    <div className="dashboard-container">

      <div className="dashboard-bg" aria-hidden="true">

        <div className="dashboard-bg-image" />

        <div className="dashboard-bg-overlay" />

        <div className="dashboard-bg-glow" />

      </div>

      <header className="dashboard-navbar">

        <div className="navbar-brand">

          <div className="navbar-logo" aria-hidden="true">

            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 384 512"
              fill="currentColor"
            >
              <path d="M318.7 268.7c-.2-36.7 16.4-64.5 50.2-85.1-18.9-27-47.4-41.9-85.1-44.9-35.7-2.8-74.8 20.8-89.1 20.8-15.2 0-50.2-19.8-77.4-19.8C61.1 140.7 0 186.4 0 279.6c0 27.5 5 55.9 15 85.1 13.4 38.7 61.7 133.4 112.1 131.8 26.4-.7 45.1-18.7 79.4-18.7 33.3 0 50.6 18.7 80 18.7 50.9-.7 94.6-86.8 107.3-125.6-72.6-34.2-75.1-100.1-75.1-102.2zM260.5 94.6c27.5-32.6 25-62.2 24.2-73.6-24.2 1.4-52.3 16.4-68.3 35-17.7 20.3-28.1 45.3-25.9 73.1 26.4 2.1 53.7-11.4 70-34.5z" />
            </svg>

          </div>

          <div className="navbar-copy">

            <h1 className="navbar-title">
              Apple Supply Chain Intelligence
            </h1>

          </div>
        </div>

        <div className="navbar-actions">

          {session?.user && (

            <div className="user-card">

              <div className="user-card-text">

                <span className="user-card-label">
                  Signed in as
                </span>

                <span className="user-card-name">
                  {session.user.username}
                </span>

              </div>

              <div className="user-avatar" aria-hidden="true">

                {session.user.username
                  .charAt(0)
                  .toUpperCase()}

              </div>
            </div>
          )}

          <button
            type="button"
            onClick={handleLogout}
            className="logout-btn"
          >

            <span>Logout</span>

            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15M12 9l-3 3m0 0 3 3m-3-3h12.75"
              />
            </svg>

          </button>
        </div>
      </header>

      <main className="dashboard-main">

        <div className="chat-wrapper">

          <div className="chat-messages">

            {messages.map((msg) => (

              <div
                key={msg.id}
                className={`message-row ${
                  msg.role === "user"
                    ? "message-row--user"
                    : "message-row--ai"
                }`}
              >

                <div
                  className={`message-bubble ${
                    msg.role === "user"
                      ? "message-bubble--user"
                      : "message-bubble--ai"
                  }`}
                >
                  {msg.content}
                </div>

              </div>
            ))}

            {isTyping && (

              <div className="message-row message-row--ai">

                <div className="message-bubble message-bubble--ai typing-indicator">

                  <div
                    className="typing-dots"
                    aria-label="Assistant is typing"
                  >

                    <span />
                    <span />
                    <span />

                  </div>
                </div>
              </div>
            )}

            <div
              ref={messagesEndRef}
              className="chat-scroll-anchor"
            />

          </div>
        </div>
      </main>

      <footer className="dashboard-footer">

        <div className="footer-inner">

          <form
            onSubmit={handleSendMessage}
            className="dashboard-input-wrapper"
          >

            <textarea
              rows={1}
              value={inputValue}
              onChange={(e) =>
                setInputValue(e.target.value)
              }
              onKeyDown={(e) => {

                if (
                  e.key === "Enter" &&
                  !e.shiftKey
                ) {

                  e.preventDefault()

                  handleSendMessage(e)
                }
              }}
              placeholder="Ask the GraphRAG assistant..."
              className="dashboard-textarea"
            />

            <button
              type="submit"
              disabled={
                !inputValue.trim() || isTyping
              }
              className="dashboard-send-btn"
              aria-label="Send message"
            >

              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >

                <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />

              </svg>

            </button>
          </form>

          <p className="footer-note">

            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >

              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-7-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0ZM9 9a.75.75 0 0 0 0 1.5h.253a.25.25 0 0 1 .244.304l-.459 2.066A1.75 1.75 0 0 0 10.747 15H11a.75.75 0 0 0 0-1.5h-.253a.25.25 0 0 1-.244-.304l.459-2.066A1.75 1.75 0 0 0 9.253 9H9Z"
                clipRule="evenodd"
              />

            </svg>

            GraphRAG may produce inaccurate information about supply chain data.
            Verify important decisions.

          </p>
        </div>
      </footer>
    </div>
  )
}