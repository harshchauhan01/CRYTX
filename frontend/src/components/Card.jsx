import "./Card.css";

export default function Card({ children, hover = true, className = "", ...props }) {
  return (
    <div className={`card ${hover ? "card-hover" : ""} ${className}`} {...props}>
      {children}
    </div>
  );
}
