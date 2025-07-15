// Form to submit email for password reset
const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/auth/password-reset/', { email });
      // Show success message
    } catch (error) {
      // Handle error
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <button type="submit">Request Reset</button>
    </form>
  );
};