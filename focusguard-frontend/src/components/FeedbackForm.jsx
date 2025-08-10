import React, { useState } from 'react';
import { toast } from 'sonner';

const FeedbackForm = ({ isOpen, onClose, username, apiBaseUrl }) => {
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!message.trim()) {
      toast.error('Please enter your feedback message');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const response = await fetch(`${apiBaseUrl}/users/${username}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subject: 'User Feedback',
          message: message,
          category: 'general',
          priority: 'medium'
        }),
      });

      if (response.ok) {
        toast.success('Feedback submitted successfully! Thank you for your input.');
        setMessage('');
        onClose();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to submit feedback');
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      toast.error('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800">📝 Submit Feedback</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Your Feedback *
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows="6"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
              placeholder="Please share your thoughts, suggestions, or report any issues..."
              required
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FeedbackForm;
