import { create } from 'zustand';
import { Product } from '@/lib/types';

export interface CartItem {
  barcode: string;
  name?: string;
  brand?: string | null;
  imageUrl?: string | null;
  addedAt: number;
}

interface CartState {
  items: CartItem[];
  isScanning: boolean;
  batchMode: boolean;
  toggleBatchMode: () => void;
  addItem: (barcode: string, metadata?: Partial<Product>) => void;
  removeItem: (barcode: string) => void;
  clearCart: () => void;
  setScanning: (scanning: boolean) => void;
}

export const useCartStore = create<CartState>((set) => ({
  items: [],
  isScanning: false,
  batchMode: false,
  
  toggleBatchMode: () => set((state) => ({ batchMode: !state.batchMode })),
  
  addItem: (barcode: string, metadata?: Partial<Product>) => set((state) => {
    // Only add if it doesn't already exist to prevent exact duplicates.
    // The cooldown prevents rapid triggering, but this is a secondary safety.
    if (state.items.some(i => i.barcode === barcode)) return state;
    
    return {
      items: [
        ...state.items, 
        {
          barcode,
          name: metadata?.name,
          brand: metadata?.brand,
          imageUrl: metadata?.image_url || undefined,
          addedAt: Date.now()
        }
      ]
    };
  }),
  
  removeItem: (barcode: string) => set((state) => ({
    items: state.items.filter(i => i.barcode !== barcode)
  })),
  
  clearCart: () => set({ items: [] }),
  
  setScanning: (scanning: boolean) => set({ isScanning: scanning }),
}));
