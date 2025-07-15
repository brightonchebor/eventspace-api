// Form to submit new password
const PasswordResetConfirm = ({ match }) => {
  const [newPassword, setNewPassword] = useState('');
  const uid = match.params.uid;
  const token = match.params.token;
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/auth/password-reset-confirm/', {
        uid,
        token,
        new_password: newPassword
      });
      // Redirect to login with success message
    } catch (error) {
      // Handle error
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input 
        type="password" 
        value={newPassword} 
        onChange={(e) => setNewPassword(e.target.value)} 
      />
      <button type="submit">Reset Password</button>
    </form>
  );
};