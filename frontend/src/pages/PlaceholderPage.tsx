import { ArrowLeft, Boxes } from "lucide-react";
import { Link } from "react-router-dom";

interface PlaceholderPageProps {
  title: string;
  description: string;
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <section className="placeholder-page">
      <div className="placeholder-page__icon">
        <Boxes size={28} />
      </div>
      <p className="eyebrow">Reserved Module</p>
      <h1>{title}</h1>
      <p>{description}</p>
      <Link className="button button--secondary" to="/dashboard">
        <ArrowLeft size={17} />
        返回 Dashboard
      </Link>
    </section>
  );
}
