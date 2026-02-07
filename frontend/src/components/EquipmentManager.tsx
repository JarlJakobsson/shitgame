import { useState, useEffect } from 'react'
import gameAPI, { Equipment, ShopInventory, GladiatorWithEquipment } from '../services/gameAPI'
import styles from './EquipmentManager.module.css'

interface EquipmentManagerProps {
  gladiator: GladiatorWithEquipment
  onGladiatorUpdate: (gladiator: GladiatorWithEquipment) => void
  onClose: () => void
}

export function EquipmentManager({ gladiator, onGladiatorUpdate, onClose }: EquipmentManagerProps) {
  const [activeTab, setActiveTab] = useState<'inventory' | 'shop'>('inventory')
  const [shopInventory, setShopInventory] = useState<ShopInventory | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const equipmentSlots = [
    { key: 'weapon', label: 'Weapon' },
    { key: 'offhand', label: 'Offhand' },
    { key: 'head', label: 'Head' },
    { key: 'shoulders', label: 'Shoulders' },
    { key: 'chest', label: 'Chest' },
    { key: 'hands', label: 'Hands' },
    { key: 'legs', label: 'Legs' },
    { key: 'feet', label: 'Feet' },
    { key: 'cape', label: 'Cape' },
    { key: 'neck', label: 'Neck' },
    { key: 'ring', label: 'Ring' },
    { key: 'amulet', label: 'Amulet' },
    { key: 'bracers', label: 'Bracers' },
    { key: 'ornament', label: 'Ornament' },
  ]

  useEffect(() => {
    if (activeTab === 'shop') {
      loadShopInventory()
    }
  }, [activeTab])

  const loadShopInventory = async () => {
    setLoading(true)
    setError('')
    try {
      const inventory = await gameAPI.getShopInventory()
      setShopInventory(inventory)
    } catch (err) {
      setError('Failed to load shop inventory')
    } finally {
      setLoading(false)
    }
  }

  const handleEquipItem = async (equipmentId: number, slot: string) => {
    setLoading(true)
    setError('')
    try {
      await gameAPI.equipItem({ equipment_id: equipmentId, slot })
      const updatedGladiator = await gameAPI.getGladiatorWithEquipment()
      onGladiatorUpdate(updatedGladiator)
    } catch (err) {
      setError('Failed to equip item')
    } finally {
      setLoading(false)
    }
  }

  const handleUnequipItem = async (slot: string) => {
    setLoading(true)
    setError('')
    try {
      await gameAPI.unequipItem(slot)
      const updatedGladiator = await gameAPI.getGladiatorWithEquipment()
      onGladiatorUpdate(updatedGladiator)
    } catch (err) {
      setError('Failed to unequip item')
    } finally {
      setLoading(false)
    }
  }

  const handlePurchaseItem = async (equipmentId: number) => {
    setLoading(true)
    setError('')
    try {
      await gameAPI.purchaseEquipment(equipmentId)
      const updatedGladiator = await gameAPI.getGladiatorWithEquipment()
      onGladiatorUpdate(updatedGladiator)
      await loadShopInventory()
    } catch (err) {
      setError('Failed to purchase item')
    } finally {
      setLoading(false)
    }
  }

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'common':
        return '#888'
      case 'rare':
        return '#0066cc'
      case 'epic':
        return '#9933cc'
      case 'legendary':
        return '#ff9900'
      default:
        return '#888'
    }
  }

  const getStatBonuses = (equipment: Equipment) => {
    const bonuses = []
    if (equipment.strength_bonus > 0) bonuses.push(`+${equipment.strength_bonus} Strength`)
    if (equipment.vitality_bonus > 0) bonuses.push(`+${equipment.vitality_bonus} Vitality`)
    if (equipment.stamina_bonus > 0) bonuses.push(`+${equipment.stamina_bonus} Stamina`)
    if (equipment.dodge_bonus > 0) bonuses.push(`+${equipment.dodge_bonus} Dodge`)
    if (equipment.initiative_bonus > 0) bonuses.push(`+${equipment.initiative_bonus} Initiative`)
    if (equipment.weaponskill_bonus > 0) bonuses.push(`+${equipment.weaponskill_bonus} Weaponskill`)
    return bonuses.join(', ')
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h2>Equipment Manager</h2>
          <div className={styles.goldDisplay}>
            Gold: {gladiator.gold}
          </div>
        </div>
        <button className={styles.closeButton} onClick={onClose}>
          Close
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'inventory' ? styles.active : ''}`}
          onClick={() => setActiveTab('inventory')}
        >
          Inventory & Equipped Items
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'shop' ? styles.active : ''}`}
          onClick={() => setActiveTab('shop')}
        >
          Equipment Shop
        </button>
      </div>

      {activeTab === 'inventory' && (
        <div className={styles.inventorySection}>
          <div className={styles.equippedItems}>
            <h3>Equipped Items</h3>
            <div className={styles.slotsGrid}>
              {equipmentSlots.map((slot) => {
                const equippedItem = gladiator.equipped_items?.[slot.key]
                return (
                  <div key={slot.key} className={styles.slot}>
                    <div className={styles.slotName}>{slot.label}</div>
                    {equippedItem ? (
                      <div className={styles.equippedItem}>
                        <div className={styles.itemName} style={{ color: getRarityColor(equippedItem.rarity) }}>
                          {equippedItem.name}
                        </div>
                        <div className={styles.itemStats}>{getStatBonuses(equippedItem)}</div>
                        <button
                          className={styles.unequipButton}
                          onClick={() => handleUnequipItem(slot.key)}
                          disabled={loading}
                        >
                          Unequip
                        </button>
                      </div>
                    ) : (
                      <div className={styles.emptySlot}>Empty</div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          <div className={styles.inventory}>
            <h3>Inventory</h3>
            <div className={styles.inventoryGrid}>
              {gladiator.inventory?.filter((item) => !item.is_equipped).map((item) => (
                <div key={item.id} className={styles.inventoryItem}>
                  <div className={styles.itemName} style={{ color: getRarityColor(item.equipment.rarity) }}>
                    {item.equipment.name}
                  </div>
                  <div className={styles.itemType}>{item.equipment.slot}</div>
                  <div className={styles.itemStats}>{getStatBonuses(item.equipment)}</div>
                  <button
                    className={styles.equipButton}
                    onClick={() => handleEquipItem(item.equipment.id, item.equipment.slot)}
                    disabled={loading}
                  >
                    Equip
                  </button>
                </div>
              ))}
              {(!gladiator.inventory || gladiator.inventory.filter((item) => !item.is_equipped).length === 0) && (
                <div className={styles.emptyInventory}>No items in inventory</div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'shop' && (
        <div className={styles.shopSection}>
          <h3>Equipment Shop</h3>
          {loading ? (
            <div className={styles.loading}>Loading shop inventory...</div>
          ) : shopInventory ? (
            <div className={styles.shopGrid}>
              {shopInventory.available_items.map((item) => (
                <div key={item.id} className={styles.shopItem}>
                  <div className={styles.itemHeader}>
                    <div className={styles.itemName} style={{ color: getRarityColor(item.rarity) }}>
                      {item.name}
                    </div>
                    <div className={styles.itemLevel}>Level {item.level_requirement}</div>
                  </div>
                  <div className={styles.itemType}>{item.slot} ({item.item_type})</div>
                  <div className={styles.itemStats}>{getStatBonuses(item)}</div>
                  <div className={styles.itemDescription}>{item.description}</div>
                  <div className={styles.itemFooter}>
                    <div className={styles.itemValue}>{item.value} gold</div>
                    <button
                      className={styles.buyButton}
                      onClick={() => handlePurchaseItem(item.id)}
                      disabled={loading || gladiator.gold < item.value}
                    >
                      {gladiator.gold < item.value ? 'Not enough gold' : 'Buy'}
                    </button>
                  </div>
                </div>
              ))}
              {shopInventory.available_items.length === 0 && (
                <div className={styles.emptyInventory}>No equipment available</div>
              )}
            </div>
          ) : (
            <div className={styles.loading}>Loading shop inventory...</div>
          )}
        </div>
      )}
    </div>
  )
}
