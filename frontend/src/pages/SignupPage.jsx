import { useState } from "react";
import { API } from "../api/api";

export default function Signup() {
  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await API.post("signup/", form);
      localStorage.setItem("token", res.data.access);
      alert("Signup successful");
    } catch (err) {
      console.error(err);
      alert("Error signing up");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Signup</h2>
      <input name="email" placeholder="Email" onChange={handleChange} />
      <input name="username" placeholder="Username" onChange={handleChange} />
      <input name="password" type="password" placeholder="Password" onChange={handleChange} />
      <button type="submit">Signup</button>
    </form>
  );
}