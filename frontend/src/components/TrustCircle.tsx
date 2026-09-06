import React from 'react';

export interface TrustContact {
  id: string;
  name: string;
  phone?: string;
  callCount: number;
  trustScore: number;
  lastSeen: string;
}

interface TrustCircleProps {
  contacts: TrustContact[];
  onAdd: (name: string, phone: string) => void;
  onRemove: (id: string) => void;
}

const TrustCircle: React.FC<TrustCircleProps> = ({ contacts, onAdd, onRemove: _onRemove }) => {
  const [isAdding, setIsAdding] = React.useState(false);
  const [newName, setNewName] = React.useState('');
  const [newPhone, setNewPhone] = React.useState('');

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (newName) {
      onAdd(newName, newPhone);
      setNewName('');
      setNewPhone('');
      setIsAdding(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-white">Trust Circle</h3>
        <button 
          onClick={() => setIsAdding(!isAdding)}
          className="text-xs bg-white/10 hover:bg-white/20 px-2 py-1 rounded transition-colors text-gray-300"
        >
          {isAdding ? 'Cancel' : '+ Add Contact'}
        </button>
      </div>

      {isAdding && (
        <form onSubmit={handleAdd} className="bg-navy-dark p-3 rounded-lg border border-white/10 space-y-3">
          <input
            type="text"
            placeholder="Name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="w-full bg-navy border border-white/10 rounded p-2 text-sm text-white focus:outline-none focus:border-electric-blue"
            required
          />
          <input
            type="text"
            placeholder="Phone (optional)"
            value={newPhone}
            onChange={(e) => setNewPhone(e.target.value)}
            className="w-full bg-navy border border-white/10 rounded p-2 text-sm text-white focus:outline-none focus:border-electric-blue"
          />
          <button type="submit" className="w-full bg-electric-blue hover:bg-electric-blue-light text-white text-sm py-1.5 rounded transition-colors">
            Save Contact
          </button>
        </form>
      )}

      <div className="space-y-2">
        {contacts.map((contact) => (
          <div key={contact.id} className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-full bg-electric-blue/20 flex items-center justify-center text-electric-blue font-bold text-sm">
                {contact.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-200">{contact.name}</p>
                <p className="text-xs text-gray-500">{contact.phone || 'No phone'}</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-green-400 font-medium">Score: {Math.round(contact.trustScore * 100)}</div>
              <div className="text-[10px] text-gray-500">{contact.callCount} calls</div>
            </div>
          </div>
        ))}
        {contacts.length === 0 && !isAdding && (
          <p className="text-sm text-gray-500 text-center py-4">No trusted contacts enrolled.</p>
        )}
      </div>
    </div>
  );
};

export default TrustCircle;
