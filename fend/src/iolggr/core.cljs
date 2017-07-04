(ns iolggr.core
  (:require
    [cljsjs.material-ui]
    [cljs-react-material-ui.core :as ui]
    [cljs-react-material-ui.icons :as ic]
    [goog.dom :as gdom]
    [cljs.core.async :as async :refer [<! >! put! chan]]
    [clojure.string :as string]
    [om.next :as om :refer-macros [defui]]
    [om.dom :as dom])
  (:require-macros [cljs.core.async.macros :refer [go]])
  (:import [goog Uri]
           [goog.net Jsonp]))

(enable-console-print!)

;; -----------------------------------------------------------------------------
;; Parsing

;         name dispatch-fn
(defmulti read om/dispatch)

; read function must return a hashmap containing a :value entry
(defmethod read :sensors
  ; the signature of a read fn is [env key params] - env is a hash map containing context & key is the requested key
  ; destructuring state from env
  [{:keys [state sensors] :as env} key params]
  (print "in read :sensors - " @state)
  {:value (:sensors @state)}
  )

(defmulti mutate om/dispatch)

; mutations return :action (function with no arguments)
; :value is the a hashmap with :keys communicates what read operations should follow a mutation
(defmethod mutate 'points/increment
  [{:keys [state]} _ {:keys [name]}]
  {:action
   (fn []
     (swap! state update-in
            [:person/by-name name :points]
            inc))})

;; -----------------------------------------------------------------------------
;; Components

;(defui Person
;  static om/Ident
;  (ident [this {:keys [name]}]
;    [:person/by-name name])
;  static om/IQuery
;  (query [this]
;    '[:name :points :age])
;  Object
;  (render [this]
;    (let [{:keys [points name] :as props} (om/props this)]
;      (ui/list-item
;        (dom/label nil (str name ", points: " points))
;        (dom/button
;          #js {:onClick
;               (fn [e]
;                 (om/transact! this
;                               `[(points/increment ~props)]))}
;          "+")
;        (dom/button
;          #js {:onClick
;               (fn [e]
;                 (om/transact! this
;                               `[(points/decrement ~props)]))}
;          "-")))
;
;    )
;  )
;https://micahasmith.github.io/2015/10/19/clojurescript-is-easy/
;https://stackoverflow.com/questions/34810803/how-do-i-use-google-charts-in-clojurescript-with-om

(defonce init-state
         {
          :drawer-open? true
          :sensors     (map #(assoc % :checked true) [
                         {:mac "1340c89be4c1" :name "Laundry"}
                         {:mac "1340c89c0a69" :name "Hallway"}
                         {:mac "1340c89ba2c7" :name "Basement"}
                         {:mac "1340c89bd3fe" :name "Outside"}
                         {:mac "1340c89bfd94" :name "Bedroom"}
                         {:mac "1340c89c2062" :name "Mobile"}
                         {:mac "1340c89bcd46" :name "Mobile2"}
                         ])
          })


(defui RootView

  static om/IQuery
  (query [this]
    [:sensors]
    )

  Object
  (render [this]
    (let
      [
       {:keys [sensors]} (om/props this)
       {:keys [drawer-open?]} (om/get-state this)
       ]
      (ui/mui-theme-provider
        {:mui-theme (ui/get-mui-theme)}
        (dom/div
          #js {:className "h-100"}
          (ui/app-bar
            {:title                         "iolggr"
             :on-left-icon-button-touch-tap #(om/set-state! this {:drawer-open? true})
             }
            )
          (ui/drawer
            {:open              drawer-open?
             :on-request-change #(om/set-state! this {:drawer-open? %})
             :docked            false}
            (ui/list
              (map
                #(ui/list-item
                   (ui/checkbox
                     {
                      :label         (get % :name)
                      :labelPosition "left"
                      :onCheck  #(om/set-state! this {:drawer-open false})
                      :checked       (get % :checked)}
                     )
                ) sensors))

            ))))))


(def reconciler
  (om/reconciler
    {:state  (atom init-state)
     :parser (om/parser {:read read :mutate mutate})}))

(om/add-root! reconciler
              RootView (gdom/getElement "app"))

